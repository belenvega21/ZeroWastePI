from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash
import re  

app = Flask(__name__)
app.secret_key = 'clave_secreta_zero_waste'  

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
    errores = {}

    if request.method == 'POST':
        correo = request.form.get('correo', '').strip()
        contraseña = request.form.get('contraseña', '').strip()

        # Validaciones
        if not correo:
            errores['correo'] = 'El correo es obligatorio.'
        elif not re.match(r"[^@]+@[^@]+\.[^@]+", correo):
            errores['correo'] = 'Ingresa un correo válido.'

        if not contraseña:
            errores['contraseña'] = 'La contraseña es obligatoria.'

        if errores:
            return render_template('login.html', errores=errores, correo=correo)

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
                errores['credenciales'] = 'Correo o contraseña incorrectos.'
                return render_template('login.html', errores=errores, correo=correo)

        except Exception as e:
            flash(f'Error en el login: {str(e)}', 'danger')

    return render_template('login.html')


# RUTA REGISTRO
@app.route('/registro', methods=['GET', 'POST'])
def registro():
    errores = {}

    if request.method == 'POST':
        try:
            nombre = request.form.get('nombre', '').strip()
            apellido = request.form.get('apellido', '').strip()
            correo = request.form.get('correo', '').strip()
            contraseña = request.form.get('contraseña', '').strip()

            # Validaciones
            if not nombre:
                errores['nombre'] = 'El nombre es obligatorio.'
            if not apellido:
                errores['apellido'] = 'El apellido es obligatorio.'
            if not correo:
                errores['correo'] = 'El correo es obligatorio.'
            elif not re.match(r"[^@]+@[^@]+\.[^@]+", correo):
                errores['correo'] = 'Ingresa un correo válido.'
            else:
                cur = mysql.connection.cursor()
                cur.execute("SELECT id FROM usuarios WHERE correo = %s", (correo,))
                if cur.fetchone():
                    errores['correo'] = 'Este correo ya está registrado.'
                cur.close()

            if not contraseña:
                errores['contraseña'] = 'La contraseña es obligatoria.'
            elif len(contraseña) < 6:
                errores['contraseña'] = 'La contraseña debe tener al menos 6 caracteres.'

            if errores:
                return render_template('registro.html', errores=errores, nombre=nombre, apellido=apellido, correo=correo)

            # Registro en BD
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

    usuario_id = session['usuario_id']

    try:
        cur = mysql.connection.cursor()
        # Consulta Obtener campañas en las que está inscrito el usuario
        cur.execute("""
            SELECT c.id, c.titulo
            FROM inscripciones i
            JOIN campañas c ON i.campaña_id = c.id
            WHERE i.usuario_id = %s
            ORDER BY c.fecha DESC
        """, (usuario_id,))
        mis_campañas = cur.fetchall()
        cur.close()

        return render_template('dashboard.html', mis_campañas=mis_campañas)

    except Exception as e:
        flash(f'Error al cargar el dashboard: {str(e)}', 'danger')
        return redirect(url_for('login'))

# RUTA DE REGISTRO DE CAMPAÑA 
@app.route('/nueva_campaña', methods=['GET', 'POST'])
def nueva_campaña():
    if 'usuario_id' not in session:
        flash('Debes iniciar sesión para continuar.', 'warning')
        return redirect(url_for('login'))

    errores = {}

    if request.method == 'POST':
        titulo = request.form.get('titulo', '').strip()
        descripcion = request.form.get('descripcion', '').strip()
        fecha = request.form.get('fecha', '').strip()
        usuario_id = session['usuario_id']

        if not titulo:
            errores['titulo'] = 'El título es obligatorio.'
        elif len(titulo) < 5:
            errores['titulo'] = 'El título debe tener al menos 5 caracteres.'

        if not descripcion:
            errores['descripcion'] = 'La descripción es obligatoria.'
        elif len(descripcion) < 10:
            errores['descripcion'] = 'Agrega una descripción más detallada.'

        if not fecha:
            errores['fecha'] = 'La fecha es obligatoria.'
        elif not re.match(r'\d{4}-\d{2}-\d{2}', fecha):
            errores['fecha'] = 'Formato de fecha inválido. Usa AAAA-MM-DD.'

        if errores:
            return render_template('nueva_campaña.html',
                                   errores=errores,
                                   titulo=titulo,
                                   descripcion=descripcion,
                                   fecha=fecha)

        try:
            cur = mysql.connection.cursor()
            cur.execute("""
                INSERT INTO campañas (titulo, descripcion, fecha, usuario_id)
                VALUES (%s, %s, %s, %s)
            """, (titulo, descripcion, fecha, usuario_id))
            mysql.connection.commit()
            cur.close()

            flash('Campaña registrada exitosamente.', 'success')
            return redirect(url_for('dashboard'))

        except Exception as e:
            flash(f'Error al registrar la campaña: {str(e)}', 'danger')
            return redirect(url_for('nueva_campaña'))

    return render_template('nueva_campaña.html',
                           errores={},
                           titulo='',
                           descripcion='',
                           fecha='')



#RUTA DE VER CAMPAÑAS (NUEVA)
@app.route('/campañas')
def ver_campañas():
    if 'usuario_id' not in session:
        flash('Debes iniciar sesión para ver campañas.', 'warning')
        return redirect(url_for('login'))

    cur = mysql.connection.cursor()
    cur.execute("SELECT id, titulo, descripcion, fecha FROM campañas WHERE estado = 1 ORDER BY fecha DESC")

    campañas = cur.fetchall()
    cur.close()

    return render_template('ver_campañas.html', campañas=campañas)


#RUTA DE INSCRIPCIÓN A CAMPAÑA (NUEVA)
@app.route('/inscribirse/<int:campana_id>', methods=['POST'])
def inscribirse_campana(campana_id):
    if 'usuario_id' not in session:
        flash('Debes iniciar sesión para inscribirte.', 'warning')
        return redirect(url_for('login'))

    usuario_id = session['usuario_id']
    cur = mysql.connection.cursor()

    # Verificar si ya está inscrito
    cur.execute("SELECT * FROM inscripciones WHERE usuario_id = %s AND campaña_id = %s", (usuario_id, campana_id))
    ya_inscrito = cur.fetchone()

    if ya_inscrito:
        flash('Ya estás inscrito en esta campaña.', 'info')
    else:
        cur.execute("INSERT INTO inscripciones (usuario_id, campaña_id) VALUES (%s, %s)", (usuario_id, campana_id))
        mysql.connection.commit()
        flash('Te has inscrito exitosamente.', 'success')

    cur.close()
    return redirect(url_for('ver_campañas'))

#VER INSCRIPCIONES(NUEVA)
@app.route('/admin/inscripciones')
@app.route('/admin/inscripciones/<int:campana_id>')
def ver_inscripciones(campaña_id=None):
    if 'usuario_id' not in session:
        flash('Debes iniciar sesión para acceder.', 'warning')
        return redirect(url_for('login'))

    try:
        cur = mysql.connection.cursor()

        if campana_id:
            cur.execute("""
                SELECT u.nombre, u.apellido, u.correo, c.titulo, i.fecha_inscripcion
                FROM inscripciones i
                JOIN usuarios u ON i.usuario_id = u.id
                JOIN campañas c ON i.campaña_id = c.id
                WHERE c.id = %s
                ORDER BY i.fecha_inscripcion DESC
            """, (campaña_id,))
        else:
            cur.execute("""
                SELECT u.nombre, u.apellido, u.correo, c.titulo, i.fecha_inscripcion
                FROM inscripciones i
                JOIN usuarios u ON i.usuario_id = u.id
                JOIN campañas c ON i.campaña_id = c.id
                ORDER BY c.titulo, i.fecha_inscripcion DESC
            """)
        
        inscripciones = cur.fetchall()
        cur.close()

        return render_template('ver_inscripciones.html', inscripciones=inscripciones)

    except Exception as e:
        flash(f'Error al cargar inscripciones: {str(e)}', 'danger')
        return redirect(url_for('dashboard'))



# LOGOUT
@app.route('/logout')
def logout():
    session.pop('usuario_id', None)
    flash('Sesión cerrada.', 'info')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
