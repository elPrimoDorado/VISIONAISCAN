import os,io, json, threading, traceback, proto, time, traductor
from enum import Enum

#imports interfaz grafica
import tkinter as tk
from tkinter.font import Font
from tkinter import *
from tkinter import ttk
from tkinter import filedialog

#dibujado
from PIL import Image, ImageDraw, ImageFont
#visionAI
from google.cloud import vision


#token
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = r'token.json'

#variables globales
listaRutaElementos = [] #diccionario de Ruta de Elementos del directorio
listaElementos = [] #diccionario de Elementos del directorio
global idioma
global ruta_directorio
hayElementos = False


class FeatureType(Enum):
    PAGE = 1
    BLOCK = 2
    PARA = 3
    WORD = 4
    SYMBOL = 5


#Metodos de GoogleAPis
def draw_boxes(image, bounds, color):
    """Draw a border around the image using the hints in the vector list."""
    draw = ImageDraw.Draw(image)
    n=1
    for bound in bounds:
        draw.polygon(
            [
                bound.vertices[0].x,
                bound.vertices[0].y,
                bound.vertices[1].x,
                bound.vertices[1].y,
                bound.vertices[2].x,
                bound.vertices[2].y,
                bound.vertices[3].x,
                bound.vertices[3].y,
            ],
            None,
            color,
            width=5
        )

        # Define el texto y la fuente
        texto = str(n)
        tamano_fuente = 48
        fuente = ImageFont.truetype('arial.ttf', tamano_fuente)

        # Obtiene el ancho y alto del texto
        text_bbox = draw.textbbox((0, 0), texto, fuente)
        ancho_texto = text_bbox[2] - text_bbox[0]
        alto_texto = text_bbox[3] - text_bbox[1]


        # Calcula el centro del rectángulo
        x_center = (bound.vertices[0].x + bound.vertices[2].x) // 2
        y_center = (bound.vertices[0].y + bound.vertices[2].y) // 2

        # Calcula las coordenadas para el texto centrado en el rectángulo
        x_texto = x_center - ancho_texto // 2
        y_texto = y_center - alto_texto // 2

        # Dibuja el texto en el centro del rectángulo, se imprime en rojo si la imagen es RGBA, de lo contrario en escala de grises será en negro
        draw.text((x_texto, y_texto), texto, font=fuente, stroke_width=2, stroke_fill="#FF0000")
        n += 1

    return image

def get_document_bounds(image_file, feature, diccionario):
    """Returns document bounds given an image."""
    client = vision.ImageAnnotatorClient()
    bounds = []
    diccionario.clear()
    with io.open(image_file, "rb") as image_file:
        content = image_file.read()

    image = vision.Image(content=content)

    response = client.document_text_detection(image=image)
    document = response.full_text_annotation

    texto_primera_pagina=""
    block_count = 1
    paragraph_count = 1
    word_count = 1

    for page in document.pages:
        for block in page.blocks:
            block_key = str(block_count)
            diccionario[block_key] = {}
            block_count += 1

            text_json = proto.Message.to_json(block.bounding_box)
            # Cargar el objeto JSON en un diccionario
            diccionario_respuesta = json.loads(text_json)

            # Obtener la lista de vertices del diccionario
            vertices = diccionario_respuesta.get("vertices", [])
            #print(vertices)

            for paragraph in block.paragraphs:
                paragraph_key = str(paragraph_count)
                diccionario[block_key][paragraph_key] = {}
                paragraph_count += 1
                for word in paragraph.words:
                    word_key = str(word_count)
                    diccionario[block_key][paragraph_key][word_key] = {}
                    word_count += 1
                    for i, symbol in enumerate(word.symbols):
                        diccionario[block_key][paragraph_key][word_key][i] = symbol.text
                        if feature == FeatureType.SYMBOL:
                            bounds.append(symbol.bounding_box)
                    if feature == FeatureType.WORD:
                        bounds.append(word.bounding_box)
                if feature == FeatureType.PARA:
                    bounds.append(paragraph.bounding_box)
            if feature == FeatureType.BLOCK:
                bounds.append(block.bounding_box)


    texto_puro=texto_primera_pagina
    #print(texto_puro)
    #print(diccionario)

    # The list `bounds` contains the coordinates of the bounding boxes.
    return bounds, diccionario

def recorrerdic(idioma, elemento, dic1):
    if idioma=='':
        idioma="es"
    print("En recorrerdic")

    texto_resultante = "Traduce solo las lineas que están en japones al español, la traduccion debe ser coherente, reemplaza el texto japones a tu traduccion sin modificar lo demás \n"
    texto_resultanteIntercalado = ""
    for block_key, block_value in dic1.items():
        # Agregar información del bloque
        texto_resultante += f"BLOQUE: {block_key}  "

        # Concatenar contenido de los párrafos dentro del bloque
        contenido_parrafos = []
        contenido_parrafosIntercalado = []
        for paragraph_key, paragraph_value in block_value.items():
            contenido_palabras = []
            for word_key, word_value in paragraph_value.items():
                contenido_simbolos = []
                for symbol_key, symbol_value in word_value.items():
                    contenido_simbolos.append(symbol_value)

                contenido_palabras.append("".join(contenido_simbolos))

            contenido_parrafos.append(" ".join(contenido_palabras))
            contenido_parrafosIntercalado.append("\n"+" ".join(contenido_palabras))

        # Unir los contenidos de los párrafos en el bloque
        contenido_bloque = "".join(contenido_parrafos)
        texto_resultante += "\n" + contenido_bloque
        texto_traducido = traductor.translate_text1(idioma, contenido_bloque)
        texto_resultante += "\n" + texto_traducido
        # Agregar un salto de línea después de cada bloque
        texto_resultante += "\n"


        #STRING INTERCALADO //COMENTADO
        #texto_resultanteIntercalado += "\n"
        #contenido_bloqueIntercalado = "".join(contenido_parrafosIntercalado)
        #texto_resultanteIntercalado += "\n" + contenido_bloqueIntercalado
        #texto_traducido2 = traductor.translate_text1(idioma, contenido_bloqueIntercalado)
        #texto_resultanteIntercalado += "\n" + texto_traducido2

    #print (texto_resultanteIntercalado)
    #txtUpdate(texto_resultante)

    with open(elemento, 'w', encoding='utf-8') as archivo:
        print("Escribiendo " + elemento)
        archivo.write(texto_resultante)
        print("cerrando " + elemento)
    print("Finalizado recorrerdic")

def render_doc_text(filein, fileout, diccionario):
    print("En renderdoctext")

    image = Image.open(filein)
    resultado = get_document_bounds(filein, FeatureType.BLOCK,diccionario)
    bounds= resultado[0]
    #diccionario1= [1]

    draw_boxes(image, bounds, "blue")

    if fileout != 0:
        image.save(fileout)
    else:
        image.show()

    print("Finalizadn renderdoctext")
    return diccionario


#interfaz grafica
def btnsubmit():

    idioma=''

    if Var1.get()==1:
        idioma = 'en'
    else:
        idioma = 'es'
    global ruta_directorio

    diccionario1 = {}
    ruta_elemento_seleccionado = os.path.join(ruta_directorio, Combo.get())
    tOriginal = Combo.get()
    nombreImagen = tOriginal[:-4] + "MOD" + tOriginal[-4:]
    ruta_elemento_salida = os.path.join(ruta_directorio, nombreImagen)
    dic1=render_doc_text(ruta_elemento_seleccionado, ruta_elemento_salida, diccionario1)

    nombreTXT= ruta_elemento_seleccionado[:-4] + ".txt"
    recorrerdic(idioma,nombreTXT,dic1)

    image1 = Image.open(ruta_elemento_salida)
    if (checkbox_value.get()):
        print("activado")
        image1.show()

    print("imagen creada")

def procesar_elemento(rutaelemento, elemento, idioma):

    try:
        
        # Agrega MOD al nombre del archivo
        ruta_elemento_salida = rutaelemento[:-4] + "MOD" + elemento[-4:]

        # Funcion enlace VisionAI
        diccionario1 = {}
        dic1 = render_doc_text(rutaelemento, ruta_elemento_salida, diccionario1)
        print("imagen creada")

        rutaNombreTXT = rutaelemento[:-4] + ".txt"
        recorrerdic(idioma, rutaNombreTXT, dic1)



    except Exception as e:
        traceback.print_exc()  # Imprimir información de la excepción

def setIdioma():
    global idioma
    idioma = ''
    if Var1.get() == 1:
        idioma = 'en'
    else:
        idioma = 'es'

def btnsubmitTodo():

    start =time.perf_counter()
    global idioma
    s1 = "\nIniciando... "
    txtUpdate(s1)

    threads = []
    for rutaelemento, elemento in zip(listaRutaElementos, listaElementos):
        thread = threading.Thread(target=procesar_elemento, args=(rutaelemento, elemento, idioma))

        thread.start()
        threads.append(thread)

    # Esperar a que todos los hilos terminen
    for thread in threads:
        thread.join()

    finish = time.perf_counter()
    t1= f' \nFinalizado en: {round(finish-start, 2)} segundos'
    txtUpdate(t1)

    print(t1)

def txtUpdate(texto):
    text.insert("end", texto)
    text.update()

def limpiarTexto():
    text.delete('1.0', "end")

def actualizar():

    listaElementos.clear()
    listaRutaElementos.clear()
    # limpiar el combobox
    Combo.configure(values=())
    # obtener ruta del label
    global ruta_directorio
    print(ruta_directorio)
    # Obtener la lista de elementos en el directorio
    listaDirectorio = os.listdir(ruta_directorio) #solo el nombre de los elementos, no la ruta completa
    # Recorrer los elementos del directorio
    for elemento in listaDirectorio:
        # Construir la ruta completa al elemento
        ruta_elemento = os.path.join(ruta_directorio, elemento)

        # Verificar si es un archivo
        if os.path.isfile(ruta_elemento):
            # Construir la ruta completa del elemento seleccionado
            listaRutaElementos.append(ruta_elemento)
            listaElementos.append(elemento)
            global hayElementos
            hayElementos=True

    Combo.configure(values=listaElementos)

def select_folder():
    limpiarTexto()
    folder_path = filedialog.askdirectory()
    global ruta_directorio
    setIdioma()
    global idioma
    ruta_directorio=folder_path
    actualizar()
    if hayElementos:
        limpiarTexto()
        change_button_style()
        txtUpdate(" Idioma : "  + idioma)
        txtUpdate("\n Carpeta seleccionada: \n " + ruta_directorio)
        txtUpdate("\n Elemento(s) agregado(s): ")
        print(listaElementos)
        for elemento in listaElementos:
            txtUpdate("\n   " + elemento)

    else:
        limpiarTexto()
        txtUpdate("\n Carpeta vacia:")

def change_button_style():
    btn_select_folder.configure(font=bold_font, fg="white", bg="green")


root = Tk()
root.title("VISIONAISCAN")
root.geometry("500x650")
root.resizable(0, 0)
frame = Frame(root)
frame.grid(row=0, column=0)

Var1 = IntVar()
RBttn = Radiobutton(frame, text="Inglés : en", variable=Var1, value=1)
RBttn.grid(row=1, column=0, padx=5, pady=5)

RBttn2 = Radiobutton(frame, text="Español : es", variable=Var1, value=2)
RBttn2.grid(row=2, column=0, padx=5, pady=5)

bold_font = Font(weight="bold")
btn_select_folder = Button(frame, text="Seleccionar carpeta", bg="red", command=select_folder)
btn_select_folder.configure(font=bold_font, fg="white")
btn_select_folder.grid(row=4, column=0, padx=(0,300), pady=(0,10))

Combo = ttk.Combobox(frame)
Combo.grid(row=4, column=0, padx=(100,0), pady=0)

btnTraducir = Button(frame, text="Traducir imagen", command=btnsubmit)
btnTraducir.grid(row=7, column=0, padx=(0,0))
btnTraducirTodo = Button(frame, text="Traducir todo", command=btnsubmitTodo)
btnTraducirTodo.grid(row=7, column=0, padx=(0,250))

checkbox_value = tk.BooleanVar(frame)
checkbox = ttk.Checkbutton(frame, text="Abrir Imagen", variable=checkbox_value)
checkbox.grid(row=7, column=0, padx=(200, 0))


text = tk.Text(frame, undo=True, height=30, width=60)
text.grid(row=9, column=0,padx=(10, 0))
text.tag_configure("left_align", justify='left')
text.config(state='normal')

root.mainloop()
