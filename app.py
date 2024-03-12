from flask import Flask, render_template, request
from flask_basicauth import BasicAuth
from ldap3 import Server, Connection, Tls
import ssl
from flask_wtf.csrf import CSRFProtect
from flask_wtf import FlaskForm
from wtforms import StringField, DateField, SelectField, SubmitField
from wtforms.validators import DataRequired


app = Flask(__name__)

csrf = CSRFProtect(app)
app.config['SECRET_KEY'] = 'some super secret key plz change me'  # use secrets

app.config['BASIC_AUTH_USERNAME'] = 'john'  # use secrets
app.config['BASIC_AUTH_PASSWORD'] = 'matrix'  # use secrets
basic_auth = BasicAuth(app)


def determine_first_digit(sex, year):
    if sex == 'male':
        if 1800 <= year <= 1899:
            return '1'
        elif 1900 <= year <= 1999:
            return '3'
        elif 2000 <= year <= 2099:
            return '5'
        elif 2100 <= year <= 2199:
            return '7'
    elif sex == 'female':
        if 1800 <= year <= 1899:
            return '2'
        elif 1900 <= year <= 1999:
            return '4'
        elif 2000 <= year <= 2099:
            return '6'
        elif 2100 <= year <= 2199:
            return '8'
    return None


def calculate_control_code(id_code_digits):
    # Define Level I and Level II weights
    level_1_weights = [1, 2, 3, 4, 5, 6, 7, 8, 9, 1]
    level_2_weights = [3, 4, 5, 6, 7, 8, 9, 1, 2, 3]

    # Calculate sum of products Level I
    sum_level_1 = sum(id_code_digit * weight for id_code_digit, weight in zip(id_code_digits, level_1_weights))
    remainder_level_1 = sum_level_1 % 11

    if remainder_level_1 < 10:
        return remainder_level_1  # Control number found with Level I weights

    # Calculate sum of products Level II if remainder from Level I is 10
    sum_level_2 = sum(id_code_digit * weight for id_code_digit, weight in zip(id_code_digits, level_2_weights))
    remainder_level_2 = sum_level_2 % 11

    if remainder_level_2 < 10:
        return remainder_level_2  # Control number found with Level II

    # Remainder from Level II is also 10, control number is 0
    return 0


def query_ldap_by_id_code(organization, id_code):
    # LDAP server address
    server_url = 'ldaps://esteid.ldap.sk.ee:636'

    # Base DN
    base_dn = f"o={organization},dc=ESTEID,c=EE"

    # Search filter using ID code
    query_filter = f"(serialNumber=PNOEE-{id_code})"

    # Setup LDAP connection without CA certificate verification
    tls_configuration = Tls(validate=ssl.CERT_NONE, version=ssl.PROTOCOL_TLS_CLIENT)
    server = Server(server_url, use_ssl=True, tls=tls_configuration)
    search_results = []  # Init empty list for search results

    try:
        # Connect to the server
        with Connection(server, auto_bind=True) as conn:
            conn.search(base_dn, query_filter, attributes=['*'])
            if conn.entries:
                for entry in conn.entries:
                    # Skip if the entry is None
                    if entry is None:
                        continue
                    # Convert entry to a dictionary and add to the results list
                    cn_value = entry.entry_attributes_as_dict['cn'][0]
                    search_results.append(cn_value)
            else:
                print("No entries found.")
    except Exception as e:
        print(f"An error occurred: {e}")

    return search_results


def generate_estonian_id_code(sex, date_of_birth, serial):
    # Determine first digit
    year = date_of_birth.year
    first_digit = determine_first_digit(sex, year)

    # Populate first 10 digits of ID code
    year_short = str(year)[2:]
    month = date_of_birth.strftime("%m")
    day = date_of_birth.strftime("%d")
    initial_id_code_str = f"{first_digit}{year_short}{month}{day}{serial}"

    # Calculate control code
    initial_id_code_digits = [int(digit) for digit in initial_id_code_str]
    control_code = calculate_control_code(initial_id_code_digits)

    # Complete ID code
    complete_id_code = f"{initial_id_code_str}{control_code}"

    return complete_id_code


class SearchForm(FlaskForm):
    code_type = SelectField('Code Type', choices=[('Identity card of Estonian citizen', 'Estonian citizen'), ('Residence card of temporary residence citizen', 'temporary resident'), ('Residence card of temporary residence citizen', 'long-term resident')], validators=[DataRequired()])
    date_of_birth = DateField('Date of Birth', format='%Y-%m-%d', validators=[DataRequired()])
    sex = SelectField('Sex', choices=[('male', 'Male'), ('female', 'Female')], validators=[DataRequired()])
    serial = StringField('Serial', validators=[DataRequired()])
    submit = SubmitField('Search')


class SearchRangeForm(FlaskForm):
    code_type = SelectField('Code Type', choices=[('Identity card of Estonian citizen', 'Estonian citizen'), ('Residence card of temporary residence citizen', 'temporary resident'), ('Residence card of temporary residence citizen', 'long-term resident')], validators=[DataRequired()])
    date_of_birth = DateField('Date of Birth', format='%Y-%m-%d', validators=[DataRequired()])
    sex = SelectField('Sex', choices=[('male', 'Male'), ('female', 'Female')], validators=[DataRequired()])
    serial_start = StringField('Serial Start', validators=[DataRequired()])
    serial_end = StringField('Serial End', validators=[DataRequired()])
    submit = SubmitField('Search')


@app.before_request
def before_request():
    if request.method in ['POST', 'PUT', 'DELETE']:
        csrf.protect()


@app.route('/')
def home():
    form_buttons = [
        {'label': 'Search', 'route': '/search'},
        {'label': 'Search in Range', 'route': '/search-range'}
    ]
    return render_template('home.html', form_buttons=form_buttons)


@app.route('/search', methods=['GET', 'POST'])
def form1():
    form = SearchForm()
    if form.validate_on_submit():
        code_type = form.code_type.data
        date_of_birth = form.date_of_birth.data
        sex = form.sex.data
        serial = form.serial.data

        complete_id_code = generate_estonian_id_code(sex, date_of_birth, serial)
        search_results = query_ldap_by_id_code(code_type, complete_id_code)
        return render_template('results.html', results=search_results)
    else:
        return render_template('ldap-form.html', form=form)


@app.route('/search-range', methods=['GET', 'POST'])
@basic_auth.required
def form2():
    form = SearchRangeForm()
    if form.validate_on_submit():
        code_type = form.code_type.data
        date_of_birth = form.date_of_birth.data
        sex = form.sex.data
        serial_start = int(form.serial_start.data)
        serial_end = int(form.serial_end.data)

        results = []
        for serial in range(serial_start, serial_end + 1):
            serial_str = f"{serial:03}"
            complete_id_code = generate_estonian_id_code(sex, date_of_birth, serial_str)
            search_results = query_ldap_by_id_code(code_type, complete_id_code)
            if search_results:
                results.extend(search_results)

        return render_template('results.html', results=results)
    else:
        return render_template('ldap-form-range.html', form=form)


@app.after_request
def after_request(response):
    response.headers["Content-Type"] = "text/html; charset=utf-8"
    return response


if __name__ == '__main__':
    app.run(debug=True)
