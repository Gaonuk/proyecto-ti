import pandas as pd
import os
##### Para cambiar los datos
# xl = pd.ExcelFile('Productos alumnos.xlsx')
# for sheet in xl.sheet_names:
#     file = pd.read_excel(xl, sheet_name=sheet)
#     file.to_csv(sheet+'.txt', index=False) 


####### Sheet 1: Productos
PRODUCTOS = {}
df_productos = pd.read_csv(os.path.join(os.path.dirname(__file__),'../INFO_SKU/Productos.txt'), sep=",",  index_col=False)
df_productos.dropna(subset = ["SKU"], inplace=True)
#print(df_productos)
for index, row in df_productos.iterrows():
    PRODUCTOS[str(int(row['SKU']))] = { 'Duración esperada (hrs)': row['Duración esperada (hrs)'],'Lote producción': \
            row['Lote producción'], 'Tiempo esperado producción (mins)': row['Tiempo esperado producción (mins)'],\
                'Grupos Productores': row['Grupos Productores'].split(",")}
print(PRODUCTOS) 
NUESTRO_SKU = [i for i in PRODUCTOS.keys() if "13" in PRODUCTOS[i]['Grupos Productores']]
print(f'NUESTROS SKUS: {NUESTRO_SKU}')

####### Sheet 2: Fórmulas producción
FORMULA = {}
FORMULA_COMPLETA = {}
df_formula = pd.read_csv(os.path.join(os.path.dirname(__file__),'../INFO_SKU/Fórmulas producción.txt'), sep=",",  index_col=False)
df_formula.dropna(subset = ["SKU Producto"], inplace=True)
#print(df_formula )
for index, row in df_formula.iterrows():
    if str(int(row['SKU Producto'])) not in FORMULA: 
        FORMULA[str(int(row['SKU Producto']))] = {str(row['SKU Ingrediente']): row['Cantidad para lote']}
    else:
        FORMULA[str(int(row['SKU Producto']))][str(row['SKU Ingrediente'])]= row['Cantidad para lote']

    if row['SKU Producto'] not in FORMULA_COMPLETA:
        FORMULA_COMPLETA[row['SKU Producto']] = {}
        FORMULA_COMPLETA[row['SKU Producto']][row['SKU Ingrediente']] = {
            'SKU Ingrediente': row['SKU Ingrediente'],
            'Nombre Ingrediente': row['Nombre Ingrediente'],
            'Cantidad': row['Cantidad'],
            'Lote producción': row['Lote producción'],
            'Cantidad para lote': row['Cantidad para lote']
        }
    else:
        FORMULA_COMPLETA[row['SKU Producto']][row['SKU Ingrediente']] = {
            'SKU Ingrediente': row['SKU Ingrediente'],
            'Nombre Ingrediente': row['Nombre Ingrediente'],
            'Cantidad': row['Cantidad'],
            'Lote producción': row['Lote producción'],
            'Cantidad para lote': row['Cantidad para lote']
        }
print(FORMULA)
print("#############################")
