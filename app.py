from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'clave_secreta_zero_waste'  # Usa una clave fuerte en producción

# Configuración MySQL
app.config['MYSQL_HOST'] = '127.0.0.1'
app.config['MYSQL_PORT'] = 3310
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = '123456'
app.config['MYSQL_DB'] = 'zero_waste'

mysql = MySQL(app)

# RUTA LOGIN
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        correo = request.form['correo']
        contraseña = request.form['contraseña']

        try:
            cur = mysql.connection.cursor()
            cur.execute("SELECT id, contraseña FROM usuarios WHERE correo = %s", (correo,))
            usuario = cur.fetchone()
            cur.close()

            if usuario and check_password_hash(usuario[1], contraseña):
                session['usuario_id'] = usuario[0]
                flash('Inicio de sesión exitoso.', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Correo o contraseña incorrectos.', 'danger')

        except Exception as e:
            flash(f'Error en el login: {str(e)}', 'danger')

    return render_template('login.html')

# RUTA REGISTRO
@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        try:
            nombre = request.form['nombre']
            apellido = request.form['apellido']
            correo = request.form['correo']
            contraseña = request.form['contraseña']
            hash_contraseña = generate_password_hash(contraseña)

            cur = mysql.connection.cursor()
            cur.execute("""
                INSERT INTO usuarios (nombre, apellido, correo, contraseña)
                VALUES (%s, %s, %s, %s)
            """, (nombre, apellido, correo, hash_contraseña))
            mysql.connection.commit()
            cur.close()

            flash('Registro exitoso. ¡Bienvenido a Zero Waste!', 'success')
            return redirect(url_for('login'))

        except Exception as e:
            flash(f'Error al registrar: {str(e)}', 'danger')
            return redirect(url_for('registro'))

    return render_template('registro.html')

# CHECK DB
@app.route('/dbcheck')
def dbcheck():
    try:
        cur = mysql.connection.cursor()
        cur.execute('SELECT 1')
        return 'Conexión exitosa con MySQL'
    except Exception as e:
        return f'Error: {str(e)}'
    
# RUTA DE DASHBOARD
@app.route('/dashboard')
def dashboard():
    if 'usuario_id' not in session:
        flash('Debes iniciar sesión para acceder.', 'warning')
        return redirect(url_for('login'))
    return render_template('dashboard.html')


# LOGOUT
@app.route('/logout')
def logout():
    session.pop('usuario_id', None)
    flash('Sesión cerrada.', 'info')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
