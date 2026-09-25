import sqlite3
import pandas as pd
import gradio as gr
from datetime import datetime

# Inicialización de la base de datos SQLite
def iniciar_bd():
    conn = sqlite3.connect("registro_pacientes.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pacientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT,
            nombre TEXT,
            edad INTEGER,
            na REAL,
            k REAL,
            cl REAL,
            hco3 REAL,
            albumina REAL,
            ag_estandar REAL,
            ag_corregido REAL,
            diagnostico TEXT,
            nivel_riesgo TEXT
        )
    ''')
    conn.commit()
    conn.close()

iniciar_bd()

def calcular_y_guardar(nombre, edad, na, k, cl, hco3, albumina):
    if not nombre or nombre.strip() == "":
        return "⚠️ Por favor ingresa el nombre del paciente.", None
    
    ag_estandar = (na + k) - (cl + hco3)
    ag_corregido = ag_estandar + (2.5 * (4.0 - albumina))
    
    if ag_corregido > 12:
        diagnostico = "Anión Gap Elevado: Acidosis metabólica por acumulación de ácidos no medidos (Cetoacidosis, Láctica, Renal, Toxinas)."
        riesgo = "🔴 Alto Riesgo / Crítico"
        color_box = "#ef4444"
    elif ag_corregido < 8:
        diagnostico = "Anión Gap Bajo: Hipoalbuminemia severa, Mieloma múltiple o intoxicación por Litio/Bromuro."
        riesgo = "🟡 Riesgo Moderado / Atípico"
        color_box = "#f59e0b"
    else:
        diagnostico = "Anión Gap Normal: Estado fisiológico normal o Acidosis Metabólica Hiperclorémica."
        riesgo = "🟢 Rango Normal / Estable"
        color_box = "#10b981"
        
    fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    conn = sqlite3.connect("registro_pacientes.db")
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO pacientes (fecha, nombre, edad, na, k, cl, hco3, albumina, ag_estandar, ag_corregido, diagnostico, nivel_riesgo)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (fecha_actual, nombre, edad, na, k, cl, hco3, albumina, round(ag_estandar, 2), round(ag_corregido, 2), diagnostico, riesgo))
    conn.commit()
    conn.close()
    
    informe_html = f"""
    <div style="padding: 15px; border-radius: 8px; border: 2px solid {color_box}; background-color: rgba(240,240,240,0.05);">
        <h3 style="margin-top:0;">Resultado del Paciente: {nombre} ({edad} años)</h3>
        <p><b>Anión Gap Estándar:</b> {ag_estandar:.2f} mEq/L</p>
        <p><b>Anión Gap Corregido (Albúmina):</b> <span style="font-size: 1.2em; font-weight: bold;">{ag_corregido:.2f} mEq/L</span></p>
        <p><b>Evaluación de Riesgo:</b> {riesgo}</p>
        <hr style="border: 0.5px solid #ccc;">
        <p><b>Interpretación Clínica:</b> {diagnostico}</p>
        <small style="color: gray;">Registro guardado exitosamente: {fecha_actual}</small>
    </div>
    """
    
    tabla_actualizada = obtener_historial()
    return informe_html, tabla_actualizada

def obtener_historial():
    conn = sqlite3.connect("registro_pacientes.db")
    df = pd.read_sql_query("SELECT fecha, nombre, edad, ag_corregido, nivel_riesgo, diagnostico FROM pacientes ORDER BY id DESC", conn)
    conn.close()
    return df

def exportar_csv():
    conn = sqlite3.connect("registro_pacientes.db")
    df = pd.read_sql_query("SELECT * FROM pacientes", conn)
    conn.close()
    ruta_archivo = "registros_pacientes_anion_gap.csv"
    df.to_csv(ruta_archivo, index=False)
    return ruta_archivo

with gr.Blocks(title="Calculadora de Anión Gap") as app:
    gr.Markdown("# 🩺 Aplicación Clínica: Calculadora de Anión Gap & Registro")
    gr.Markdown("Herramienta médica para evaluación metabólica con persistencia de datos independiente.")
    
    with gr.Tab("Nueva Evaluación"):
        with gr.Row():
            with gr.Column():
                gr.Markdown("### Datos del Paciente")
                input_nombre = gr.Textbox(label="Nombre Completo", placeholder="Ej. Juan Pérez")
                input_edad = gr.Number(label="Edad", value=45, precision=0)
                
                gr.Markdown("### Electrólitos y Albúmina (mEq/L - g/dL)")
                input_na = gr.Slider(100, 180, value=140, label="Sodio (Na+)", step=1)
                input_k = gr.Slider(1.0, 10.0, value=4.0, label="Potasio (K+)", step=0.1)
                input_cl = gr.Slider(70, 140, value=104, label="Cloro (Cl-)", step=1)
                input_hco3 = gr.Slider(5, 50, value=24, label="Bicarbonato (HCO3-)", step=1)
                input_alb = gr.Slider(1.0, 6.0, value=4.0, label="Albúmina (g/dL)", step=0.1)
                
                btn_calcular = gr.Button("⚡ Calcular y Registrar", variant="primary")
                
            with gr.Column():
                gr.Markdown("### Diagnóstico e Informe")
                output_reporte = gr.HTML(value="<p style='color:gray;'>Ingrese los datos del paciente y presione 'Calcular y Registrar'.</p>")
    
    with gr.Tab("Historial de Pacientes"):
        gr.Markdown("### Registro de Pacientes")
        btn_refrescar = gr.Button("🔄 Actualizar Tabla")
        tabla_registros = gr.Dataframe(value=obtener_historial(), interactive=False)
        btn_exportar = gr.Button("📥 Descargar Base de Datos (CSV)")
        archivo_descarga = gr.File(label="Archivo listo para descarga")

    btn_calcular.click(
        fn=calcular_y_guardar,
        inputs=[input_nombre, input_edad, input_na, input_k, input_cl, input_hco3, input_alb],
        outputs=[output_reporte, tabla_registros]
    )
    
    btn_refrescar.click(
        fn=obtener_historial,
        inputs=[],
        outputs=[tabla_registros]
    )
    
    btn_exportar.click(
        fn=exportar_csv,
        inputs=[],
        outputs=[archivo_descarga]
    )

app.launch(server_name="0.0.0.0", server_port=7860)
