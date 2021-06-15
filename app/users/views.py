from flask import render_template, Blueprint, request, redirect, url_for, flash, Markup, abort, session, Response
from sqlalchemy.exc import IntegrityError
from flask_login import login_user, current_user, login_required, logout_user
from itsdangerous import URLSafeTimedSerializer
from threading import Thread
from flask_mail import Message
from datetime import datetime, timedelta
from authy.api import AuthyApiClient
from .forms import RegisterForm, LoginForm, EmailForm, PasswordForm
from app import app, db, mail
from app.models import User


# CONFIG
users_blueprint = Blueprint('users', __name__, template_folder='templates')
# HELPERS
def send_async_email(msg):
    with app.app_context():
        mail.send(msg)


def send_email(subject, recipients, html_body):
    msg = Message(subject, recipients=recipients)
    msg.html = html_body
    thr = Thread(target=send_async_email, args=[msg])
    thr.start()


def send_confirmation_email(user_email):
    confirm_serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])

    confirm_url = url_for(
        'users.confirm_email',
        token=confirm_serializer.dumps(user_email, salt='email-confirmation-salt'),
        _external=True)

    html = render_template(
        'email_confirmation.html',
        confirm_url=confirm_url)

    send_email('Confirm Your Email Address', [user_email], html)


def send_password_reset_email(user_email):
    password_reset_serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])

    password_reset_url = url_for(
        'users.reset_with_token',
        token=password_reset_serializer.dumps(user_email, salt='password-reset-salt'),
        _external=True)

    html = render_template(
        'email_password_reset.html',
        password_reset_url=password_reset_url)

    send_email('Password Reset Requested', [user_email], html)

# ROUTES
@users_blueprint.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST':
        if form.validate_on_submit():
            try:
                new_user = User(form.email.data, form.password.data)
                new_user.authenticated = True
                db.session.add(new_user)
                db.session.commit()
                send_confirmation_email(new_user.email)
                message = Markup(
                    "<strong>Success!</strong> Thanks for registering. Please check your email to confirm your email address.")
                flash(message, 'success')
                return redirect(url_for('home'))
            except IntegrityError:
                db.session.rollback()
                message = Markup(
                    "<strong>Error!</strong> Unable to process registration.")
                flash(message, 'danger')
    return render_template('register.html', form=form)


@users_blueprint.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm(request.form)
    if request.method == 'POST':
        if form.validate_on_submit():
            user = User.query.filter_by(email=form.email.data).first()
            if user is not None and user.is_correct_password(form.password.data):
                if user.is_email_confirmed is not True:
                    user.authenticated = True
                    db.session.add(user)
                    db.session.commit()
                    login_user(user)
                    return redirect(url_for('users.resend_email_confirmation'), )
                if user.is_email_confirmed is True:
                    user.authenticated = True
                    user.last_logged_in = user.current_logged_in
                    user.current_logged_in = datetime.now()
                    db.session.add(user)
                    db.session.commit()
                    login_user(user)
                    message = Markup(
                        "<strong>Chào mừng bạn trở lại!</strong> Bây giờ bạn đã đăng nhập thành công.")
                    flash(message, 'success')
                    return redirect(url_for('home'))
            else:
                message = Markup(
                    "<strong>Error!</strong> Thông tin đăng nhập không chính xác.")
                flash(message, 'danger')
    return render_template('login.html', form=form)


@users_blueprint.route('/user_profile', methods=['GET', 'POST'])
@login_required
def user_profile():
    return render_template('user_profile.html')


@users_blueprint.route('/confirm/<token>')
def confirm_email(token):
    try:
        confirm_serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
        email = confirm_serializer.loads(token, salt='email-confirmation-salt', max_age=3600)
    except:
        message = Markup(
            "Liên kết xác nhận không hợp lệ hoặc đã hết hạn.")
        flash(message, 'danger')
        return redirect(url_for('users.login'))

    user = User.query.filter_by(email=email).first()

    if user.email_confirmed:
        message = Markup(
            "Tài khoản đã được xác nhận. Xin vui lòng đăng nhập.")
        flash(message, 'info')
    else:
        user.email_confirmed = True
        user.email_confirmed_on = datetime.now()
        db.session.add(user)
        db.session.commit()
        message = Markup(
            "Cảm ơn bạn đã xác nhận địa chỉ email của mình!")
        flash(message, 'success')

    return redirect(url_for('home'))


@users_blueprint.route('/reset', methods=["GET", "POST"])
def reset():
    form = EmailForm()
    if form.validate_on_submit():
        try:
            user = User.query.filter_by(email=form.email.data).first_or_404()
        except:
            message = Markup(
                "Invalid email address!")
            flash(message, 'danger')
            return render_template('password_reset_email.html', form=form)
        if user.email_confirmed:
            send_password_reset_email(user.email)
            message = Markup(
                "Vui lòng kiểm tra email của bạn để biết liên kết đặt lại mật khẩu.")
            flash(message, 'success')
        else:
            message = Markup(
                "Địa chỉ email của bạn phải được xác nhận trước khi thử đặt lại mật khẩu.")
            flash(message, 'danger')
        return redirect(url_for('users.login'))

    return render_template('password_reset_email.html', form=form)


@users_blueprint.route('/reset/<token>', methods=["GET", "POST"])
def reset_with_token(token):
    try:
        password_reset_serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
        email = password_reset_serializer.loads(token, salt='password-reset-salt', max_age=3600)
    except:
        message = Markup(
            "Liên kết đặt lại mật khẩu không hợp lệ hoặc đã hết hạn.")
        flash(message, 'danger')
        return redirect(url_for('users.login'))

    form = PasswordForm()

    if form.validate_on_submit():
        try:
            user = User.query.filter_by(email=email).first_or_404()
        except:
            message = Markup(
                "Địa chỉ email không hợp lệ!")
            flash(message, 'danger')
            return redirect(url_for('users.login'))

        user.password = form.password.data
        db.session.add(user)
        db.session.commit()
        message = Markup(
            "Mật khẩu của bạn đã được cập nhật!")
        flash(message, 'success')
        return redirect(url_for('users.login'))

    return render_template('reset_password_with_token.html', form=form, token=token)


@users_blueprint.route('/admin_view_users')
@login_required
def admin_view_users():
    if current_user.role != 'admin':
        abort(403)
    else:
        users = User.query.order_by(User.id).all()
        return render_template('admin_view_users.html', users=users)


@users_blueprint.route('/admin_dashboard')
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        abort(403)
    else:
        users = User.query.order_by(User.id).all()
        kpi_mau = User.query.filter(User.last_logged_in > (datetime.today() - timedelta(days=30))).count()
        kpi_total_confirmed = User.query.filter_by(email_confirmed=True).count()
        kpi_mau_percentage = (100 / kpi_total_confirmed) * kpi_mau
        return render_template('admin_dashboard.html', users=users, kpi_mau=kpi_mau, kpi_total_confirmed=kpi_total_confirmed, kpi_mau_percentage=kpi_mau_percentage)


@users_blueprint.route('/logout')
@login_required
def logout():
    user = current_user
    user.authenticated = False
    db.session.add(user)
    db.session.commit()
    logout_user()
    message = Markup("<strong>Goodbye!</strong> Bạn đã đăng xuất.")
    flash(message, 'info')
    return redirect(url_for('users.login'))


@users_blueprint.route('/password_change', methods=["GET", "POST"])
@login_required
def user_password_change():
    form = PasswordForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            user = current_user
            user.password = form.password.data
            db.session.add(user)
            db.session.commit()
            message = Markup(
                "Mật khẩu đã được cập nhật!")
            flash(message, 'success')
            return redirect(url_for('users.user_profile'))

    return render_template('password_change.html', form=form)


@users_blueprint.route('/resend_confirmation')
@login_required
def resend_email_confirmation():
    try:
        send_confirmation_email(current_user.email)
        message = Markup(
            "Email được gửi để xác nhận địa chỉ email của bạn. Hãy kiểm tra hộp thư đến của bạn!")
        flash(message, 'success')
        user = current_user
        user.authenticated = False
        db.session.add(user)
        db.session.commit()
        logout_user()
    except IntegrityError:
        message = Markup(
            "Error!  Unable to send email to confirm your email address.")
        flash(message, 'danger')
        user = current_user
        user.authenticated = False
        db.session.add(user)
        db.session.commit()
        logout_user()
    return redirect(url_for('users.login'))


@users_blueprint.route('/email_change', methods=["GET", "POST"])
@login_required
def user_email_change():
    form = EmailForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            try:
                user_check = User.query.filter_by(email=form.email.data).first()
                if user_check is None:
                    user = current_user
                    user.email = form.email.data
                    user.email_confirmed = False
                    user.email_confirmed_on = None
                    user.email_confirmation_sent_on = datetime.now()
                    db.session.add(user)
                    db.session.commit()
                    send_confirmation_email(user.email)
                    message = Markup(
                        "Email changed!  Please confirm your new email address (link sent to new email)")
                    flash(message, 'success')
                    return redirect(url_for('users.user_profile'))
                else:
                    message = Markup(
                        "Sorry, that email already exists!")
                    flash(message, 'danger')
            except IntegrityError:
                message = Markup(
                    "Sorry, that email already exists!")
                flash(message, 'danger')
    return render_template('email_change.html', form=form)
#----------------------
# OTP
#----------------------
api = AuthyApiClient(app.config['AUTHY_API_KEY'])

@users_blueprint.route('/step1/phone_verification', methods=["GET", "POST"])
@login_required
def phone_verification():
    if request.method == 'POST':
        phone_number = request.form.get('phone')
        session['phone_number'] = phone_number
        api.phones.verification_start(phone_number, country_code=+84, via='sms')
        print(phone_number)
        return redirect(url_for('users.verify_otp'))

    return render_template('phone_verification.html')

@users_blueprint.route('/step2/verify_otp', methods=["GET", "POST"])
@login_required
def verify_otp():
    if request.method == 'POST':
        ist = request.form.get('ist')
        sec = request.form.get('sec')
        third = request.form.get('third')
        fourth = request.form.get('fourth')
        token = ist + sec + third + fourth
        phone_number = session.get('phone_number')
        print(phone_number)
        verification = api.phones.verification_check(phone_number, country_code=+84,verification_code=token)

        if verification.ok():
            message = Markup(
                "OTP chinh xac")
            flash(message, 'success')
            return redirect(url_for('users.idcard_verification'))
        else:
            message = Markup(
                "OTP khong chinh xac")
            flash(message, 'danger')
            return redirect(url_for('users.phone_verification'))

    return render_template('otp.html')
#-------------------------------
# nhan dien chung minh thu
#-------------------------------
import time
import os
from ocr.reader.reader import *
from werkzeug.utils import secure_filename
import sys

#APP_ROOT = os.path.dirname(os.path.abspath(__file__))
#app.config['IMAGE_UPLOADS'] = os.path.join(APP_ROOT, 'static')

@users_blueprint.route('/step3/idcard_verification', methods=["GET", "POST"])
@login_required
def idcard_verification():
    if request.method == 'POST':
        if request.files:
            image = request.files['image']
            if image.filename == "":
                print('No file selected')
                return redirect(request.url)
            if allowed_image(image.filename):
                filename = secure_filename(image.filename)
                print(filename)
                image.save(os.path.join(app.config["IMAGE_UPLOADS"], filename))
                reoriented_img = reorient_image(os.path.join(app.config["IMAGE_UPLOADS"], filename))
                reoriented_img.save(os.path.join(app.config["IMAGE_UPLOADS"], filename))
                return redirect(url_for("users.predict", filename=filename))
            else:
                return redirect(request.url)
    return render_template('idcard_verification.html')
#---------------------------------
app.config["ALLOWED_IMAGE_EXTENSIONS"] = ["JPEG", "JPG", "PNG", "GIF"]
def allowed_image(filename):

    if "." not in filename:
        return False

    ext = filename.rsplit(".", 1)[1]

    if ext.upper() in app.config["ALLOWED_IMAGE_EXTENSIONS"]:
        return True
    else:
        return False
def reorient_image(im):
    im = Image.open(im)
    try:
        image_exif = im._getexif()
        image_orientation = image_exif[274]
        print(image_orientation)
        if image_orientation in (2, '2'):
            return im.transpose(Image.FLIP_LEFT_RIGHT)
        elif image_orientation in (3, '3'):
            return im.transpose(Image.ROTATE_180)
        elif image_orientation in (4, '4'):
            return im.transpose(Image.FLIP_TOP_BOTTOM)
        elif image_orientation in (5, '5'):
            return im.transpose(Image.ROTATE_90).transpose(Image.FLIP_TOP_BOTTOM)
        elif image_orientation in (6, '6'):
            return im.transpose(Image.ROTATE_270)
        elif image_orientation in (7, '7'):
            return im.transpose(Image.ROTATE_270).transpose(Image.FLIP_TOP_BOTTOM)
        elif image_orientation in (8, '8'):
            return im.transpose(Image.ROTATE_90)
        else:
            return im
    except (KeyError, AttributeError, TypeError, IndexError):
        return im
#----------------------------
@users_blueprint.route('/step3/idcard_verification/<filename>', methods=["GET", "POST"])
@login_required
def predict(filename):
    start = time.time()
    #Crop image
    filepath = app.config["IMAGE_UPLOADS"] + "/" + filename

    img, original_image, original_width, original_height = preprocess_image(filepath, Cropper.TARGET_SIZE)
    cropper = Cropper()
    cropper.set_image(original_image=original_image)
    # output of cropper part
    aligned_image = getattr(cropper, "image_output")
    cv2.imwrite('app/static/aligned_images/' + filename, aligned_image)
    warped = cv2.cvtColor(aligned_image, cv2.COLOR_BGR2RGB)
    if warped is None:
        print('Cant find id card in image')
        return render_template('idcard_verification.html')
    try:
        face, number_img, name_img, dob_img, \
        country_img, address_img, country_img_list, address_img_list = detect_info(
            warped)
    except:
        print('Cant find id card in image')
        sys.exit()
    list_image = [face, number_img, name_img, dob_img, country_img, address_img]
    for y in range(len(list_image)):
        plt.subplot(len(list_image), 1, y + 1)
        plt.imshow(list_image[y])


    face =Image.fromarray(face)
    warped = Image.fromarray(warped)

    face.save(os.path.join(app.config["IMAGE_UPLOADS2"], filename))
    warped.save(os.path.join(app.config["IMAGE_UPLOADS3"], filename))

    number_text = get_text(number_img)
    name_text = get_text(name_img)
    dob_text = get_dob_text(dob_img)
    country_text = process_list_img(country_img_list,is_country=True)
    address_text = process_list_img(address_img_list,is_country=False)
    print("Thời gian chạy:{}".format(time.time() - start))
    print(f'''
        'Số: {number_text} ',
        'Họ và tên: {name_text} ',
        'Ngày tháng năm sinh: {dob_text} ',
        'Nguyên quán: {country_text} ',
        'Hộ khẩu thường trú: {address_text} '
        ''')
    session["filename"] = filename
    return render_template("idcard_verification.html",id=number_text, full_name=name_text,

                           date_of_birth=dob_text,que_quan = country_text,noi_thuong_tru=address_text,filename=str(filename))

#------------------------------------------------
from face_matching.core.utils import *
from imutils.video import WebcamVideoStream
@users_blueprint.route('/step4/face_verification', methods=["GET", "POST"])
@login_required
def face_verification():
    if request.method == 'POST':
        f1 = "C:\\Users\\kinhk\\PycharmProjects\\DoAnTotNgiep\\app\\static\\alignid_images\\ddd2.jpg"
        #filename = str(filename)
        #print(filename)
        #f1 = app.config["IMAGE_UPLOADS"] + "/" + filename
       # print(f1)
        f2 = request.files['pic']
        f2.save("C:\\Users\\kinhk\\PycharmProjects\\DoAnTotNgiep\\app\\static\\face_detection\\" + secure_filename(f2.filename))
        f1e = embedding(f1)
        f2e = embedding("C:\\Users\\kinhk\\PycharmProjects\\DoAnTotNgiep\\app\\static\\face_detection\\" + secure_filename(f2.filename))
        text = is_match(f1e,f2e)
        print(text)
        f = open('result.txt', 'w+')
        if text == "match":
            print("Xác minh thành công kyc")

            return render_template("resullt_kyc.html", result =1)
        else:
            print("Vui lòng thử lại")
            return render_template('home.html')
    return render_template("face_verification.html" )







@users_blueprint.route('/step4', methods=["GET", "POST"])
@login_required
def camera():

    return redirect(url_for('users.step4'))

@users_blueprint.route('/result', methods=["GET", "POST"])
@login_required
def step4():
    return render_template("resullt_kyc.html")
