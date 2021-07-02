import pandas as pd

##### Para cambiar los datos
# xl = pd.ExcelFile('Productos alumnos.xlsx')
# for sheet in xl.sheet_names:
#     file = pd.read_excel(xl, sheet_name=sheet)
#     file.to_csv(sheet+'.txt', index=False) 


####### Sheet 1: Productos
productos = {}
df_productos = pd.read_csv('2021-1-proyecto-grupo-13\INFO_SKU\Productos.txt', sep=",",  index_col=False)
df_productos.dropna(subset = ["SKU"], inplace=True)
#print(df_productos)
for index, row in df_productos.iterrows():
    productos[str(int(row['SKU']))] = {'Nombre': row['Nombre'], 'Descripción': row['Descripción'], 'Costo producción lote': \
        row['Costo producción lote'], 'Duración esperada (hrs)': row['Duración esperada (hrs)'],'Lote producción': \
            row['Lote producción'], 'Tiempo esperado producción (mins)': row['Tiempo esperado producción (mins)'],\
                'Grupos Productores': [row['Grupos Productores']]}
print(productos['100'], '\n', productos['10001'])
print("#############################")

####### Sheet 2: Fórmulas producción
formula  = {}
df_formula  = pd.read_csv('2021-1-proyecto-grupo-13\INFO_SKU\Fórmulas producción.txt', sep=",",  index_col=False)
df_formula .dropna(subset = ["SKU Producto"], inplace=True)
#print(df_formula )
for index, row in df_formula .iterrows():
    if str(int(row['SKU Producto'])) not in formula: 
        formula [str(int(row['SKU Producto']))] = [{'SKU Ingrediente': row['SKU Ingrediente'], 'Nombre Ingrediente': row['Nombre Ingrediente'],\
             'Cantidad': row['Cantidad'], 'Lote producción': row['Lote producción'],'Cantidad para lote': row['Cantidad para lote']}]
    else:
        formula [str(int(row['SKU Producto']))].append({'SKU Ingrediente': row['SKU Ingrediente'], 'Nombre Ingrediente': row['Nombre Ingrediente'],\
             'Cantidad': row['Cantidad'], 'Lote producción': row['Lote producción'],'Cantidad para lote': row['Cantidad para lote']})
print(formula)
print("#############################")

####### Sheet 3: Resumen fórmulas
resumen = {}
df_resumen = pd.read_csv('2021-1-proyecto-grupo-13\INFO_SKU\Resumen fórmulas.txt', sep=",",  index_col=False)
df_resumen.dropna(subset = ["SKU"], inplace=True)
for index, row in df_resumen.iterrows():
    resumen[str(int(row['SKU']))] = {'Productos para producir': row['Productos para producir'],\
         'Espacio para recibir producción': row['Espacio para recibir producción']}
print(resumen['100'], '\n', resumen['10001'])