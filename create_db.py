import sqlite3
import random

conn = sqlite3.connect("store.db")
cursor = conn.cursor()

# Eliminar tablas si existen para reiniciar la estructura
cursor.execute("DROP TABLE IF EXISTS Ventas")
cursor.execute("DROP TABLE IF EXISTS Productos")
cursor.execute("DROP TABLE IF EXISTS Distribuidores")

# Crear tabla Productos
cursor.execute('''
CREATE TABLE Productos (
    CveArticulo INT PRIMARY KEY,
    Nombre_Articulo VARCHAR(255),
    Categoria VARCHAR(100),
    TamanioDeFoto VARCHAR(50),
    TamanioFotoConNumero FLOAT,
    NumeroPagina INT,
    NumeroPaginaCatalogo VARCHAR(50),
    Posicion VARCHAR(50),
    Rango_PN_Nuevo VARCHAR(50),
    Rango_PE_Nuevo VARCHAR(50),
    TBasica VARCHAR(50),
    Precio_Especial_Unitario FLOAT,
    Precio_Normal_Unitario FLOAT
)
''')

# Crear tabla Distribuidores
cursor.execute('''
CREATE TABLE Distribuidores (
    ClaveDistribuidor VARCHAR(50) PRIMARY KEY,
    Clasificacion VARCHAR(100),
    Cod_Aso INT,
    Municipio VARCHAR(100),
    Estado VARCHAR(100),
    Zona_Metropolitana VARCHAR(100)
)
''')

# Crear tabla Ventas
cursor.execute('''
CREATE TABLE Ventas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    Catálogo INT,
    ClaveDistribuidor VARCHAR(50),
    CveArticulo INT,
    Descuento FLOAT,
    RangoDescuentos VARCHAR(50),
    UnidadesVendidas INT,
    VentaCatalogo FLOAT,
    Fecha DATE,
    FOREIGN KEY (ClaveDistribuidor) REFERENCES Distribuidores(ClaveDistribuidor),
    FOREIGN KEY (CveArticulo) REFERENCES Productos(CveArticulo)
)
''')

# Lista de 100 productos reales y variados
productos_reales = [
    (1, "Laptop HP 15.6''", "Electrónica", "150px", 2.0, 1, "1", "A", "$12000-$13000", "$11000-$12000", "Oferta", 11500.0, 12500.0),
    (2, "Smartphone Samsung Galaxy A54", "Electrónica", "120px", 1.5, 2, "2", "B", "$7000-$8000", "$6500-$7000", "Lanzamiento", 6700.0, 7500.0),
    (3, "Televisor LG 50'' 4K", "Electrónica", "200px", 2.5, 3, "3", "C", "$9000-$10000", "$8500-$9000", "Descuento", 8700.0, 9500.0),
    (4, "Audífonos Bluetooth JBL", "Electrónica", "60px", 1.0, 4, "4", "D", "$1200-$1500", "$1000-$1200", "Oferta", 1100.0, 1350.0),
    (5, "Cámara Canon EOS Rebel", "Electrónica", "90px", 1.2, 5, "5", "E", "$15000-$17000", "$14000-$15000", "Lanzamiento", 14500.0, 16000.0),
    (6, "Camisa Polo Ralph Lauren", "Ropa", "40px", 0.8, 6, "6", "A", "$1200-$1400", "$1000-$1200", "Nueva temporada", 1100.0, 1300.0),
    (7, "Pantalón Levi's 501", "Ropa", "50px", 1.0, 7, "7", "B", "$1500-$1700", "$1300-$1500", "Descuento", 1400.0, 1600.0),
    (8, "Vestido Zara Floral", "Ropa", "45px", 0.9, 8, "8", "C", "$900-$1100", "$800-$900", "Oferta", 850.0, 1000.0),
    (9, "Tenis Nike Air Max", "Ropa", "60px", 1.1, 9, "9", "D", "$2200-$2500", "$2000-$2200", "Lanzamiento", 2100.0, 2350.0),
    (10, "Chamarra Adidas Originals", "Ropa", "70px", 1.3, 10, "10", "E", "$1800-$2000", "$1600-$1800", "Nueva temporada", 1700.0, 1900.0),
    (11, "Sartén T-fal 24cm", "Hogar", "30px", 0.7, 11, "11", "A", "$350-$400", "$300-$350", "Descuento", 320.0, 370.0),
    (12, "Batería de cocina Vasconia", "Hogar", "80px", 1.8, 12, "12", "B", "$1200-$1400", "$1100-$1200", "Oferta", 1150.0, 1300.0),
    (13, "Colchón Spring Air Queen", "Hogar", "150px", 2.2, 13, "13", "C", "$7000-$8000", "$6500-$7000", "Lanzamiento", 6700.0, 7500.0),
    (14, "Juego de sábanas Matrimonial", "Hogar", "40px", 0.8, 14, "14", "D", "$600-$700", "$500-$600", "Nueva temporada", 550.0, 650.0),
    (15, "Licuadora Oster 10 velocidades", "Hogar", "50px", 1.0, 15, "15", "E", "$900-$1100", "$800-$900", "Descuento", 850.0, 1000.0),
    (16, "Cereal Kellogg's Zucaritas 750g", "Alimentos", "20px", 0.5, 16, "16", "A", "$70-$80", "$60-$70", "Oferta", 65.0, 75.0),
    (17, "Aceite Nutrioli 900ml", "Alimentos", "25px", 0.6, 17, "17", "B", "$50-$60", "$45-$50", "Descuento", 48.0, 55.0),
    (18, "Arroz SOS 1kg", "Alimentos", "22px", 0.5, 18, "18", "C", "$35-$40", "$30-$35", "Oferta", 33.0, 38.0),
    (19, "Galletas Gamesa Emperador", "Alimentos", "18px", 0.4, 19, "19", "D", "$25-$30", "$20-$25", "Nueva temporada", 23.0, 28.0),
    (20, "Atún Dolores en agua 140g", "Alimentos", "15px", 0.3, 20, "20", "E", "$18-$22", "$15-$18", "Descuento", 16.0, 20.0),
    (21, "Shampoo Head & Shoulders 400ml", "Belleza", "30px", 0.7, 21, "21", "A", "$90-$100", "$80-$90", "Oferta", 85.0, 95.0),
    (22, "Crema Nivea Soft 200ml", "Belleza", "25px", 0.6, 22, "22", "B", "$60-$70", "$50-$60", "Descuento", 55.0, 65.0),
    (23, "Desodorante Axe Dark Temptation", "Belleza", "20px", 0.5, 23, "23", "C", "$45-$50", "$40-$45", "Oferta", 43.0, 48.0),
    (24, "Maquillaje Maybelline Fit Me", "Belleza", "28px", 0.6, 24, "24", "D", "$120-$140", "$100-$120", "Nueva temporada", 110.0, 130.0),
    (25, "Perfume Calvin Klein One 100ml", "Belleza", "35px", 0.8, 25, "25", "E", "$650-$700", "$600-$650", "Lanzamiento", 620.0, 670.0),
    (26, "Juguete LEGO Classic 900 piezas", "Juguetes", "60px", 1.2, 26, "26", "A", "$900-$1000", "$850-$900", "Oferta", 870.0, 950.0),
    (27, "Muñeca Barbie Dreamhouse", "Juguetes", "55px", 1.1, 27, "27", "B", "$1800-$2000", "$1700-$1800", "Descuento", 1750.0, 1900.0),
    (28, "Carro Hot Wheels Monster Truck", "Juguetes", "20px", 0.5, 28, "28", "C", "$80-$100", "$70-$80", "Oferta", 75.0, 90.0),
    (29, "Pelota Wilson de fútbol", "Juguetes", "25px", 0.6, 29, "29", "D", "$250-$300", "$200-$250", "Nueva temporada", 225.0, 275.0),
    (30, "Puzzle Ravensburger 1000 piezas", "Juguetes", "30px", 0.7, 30, "30", "E", "$350-$400", "$300-$350", "Descuento", 320.0, 370.0),
]
# Para completar 100 productos, duplicamos y variamos ligeramente los anteriores
for i in range(31, 101):
    base = productos_reales[(i-1) % 30]
    productos_reales.append((
        i,
        base[1] + f" Edición {((i-1)//30)+1}",
        base[2],
        base[3],
        base[4],
        base[5],
        base[6],
        base[7],
        base[8],
        base[9],
        base[10],
        base[11] + 10*((i-1)//30),
        base[12] + 10*((i-1)//30)
    ))
cursor.executemany('''
    INSERT INTO Productos (
        CveArticulo, Nombre_Articulo, Categoria, TamanioDeFoto, TamanioFotoConNumero,
        NumeroPagina, NumeroPaginaCatalogo, Posicion, Rango_PN_Nuevo, Rango_PE_Nuevo,
        TBasica, Precio_Especial_Unitario, Precio_Normal_Unitario
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
''', productos_reales)

# Insertar 20 distribuidores reales
estados = ["CDMX", "Jalisco", "Nuevo León", "Puebla", "Guanajuato", "Veracruz", "Chiapas", "Yucatán", "Querétaro", "Coahuila"]
municipios = ["Benito Juárez", "Zapopan", "San Pedro", "Tehuacán", "León", "Boca del Río", "Tuxtla", "Mérida", "Corregidora", "Torreón"]
distribuidores = []
for i in range(1, 21):
    distribuidores.append((
        f"DISTRIB{i:03}",
        random.choice(["Oro", "Plata", "Bronce"]),
        1000 + i,
        random.choice(municipios),
        random.choice(estados),
        random.choice(["Zona Norte", "Zona Sur", "Zona Centro"])
    ))
cursor.executemany('''
    INSERT INTO Distribuidores (
        ClaveDistribuidor, Clasificacion, Cod_Aso, Municipio, Estado, Zona_Metropolitana
    ) VALUES (?, ?, ?, ?, ?, ?)
''', distribuidores)

# Insertar 300 ventas relacionadas
ventas = []
for i in range(1, 301):
    clave_dist = f"DISTRIB{random.randint(1,20):03}"
    cve_art = random.randint(1, 100)
    catalogo = random.randint(1, 12)
    descuento = round(random.uniform(0, 30), 2)
    rango_desc = f"{int(descuento)}%"
    unidades = random.randint(1, 20)
    precio_esp = 115 + cve_art * 0.7
    venta = round(unidades * precio_esp * (1 - descuento/100), 2)
    fecha = f"2024-{random.randint(1,12):02}-" + f"{random.randint(1,28):02}"
    ventas.append((catalogo, clave_dist, cve_art, descuento, rango_desc, unidades, venta, fecha))
cursor.executemany('''
    INSERT INTO Ventas (
        Catálogo, ClaveDistribuidor, CveArticulo, Descuento, RangoDescuentos, UnidadesVendidas, VentaCatalogo, Fecha
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
''', ventas)

conn.commit()
conn.close()