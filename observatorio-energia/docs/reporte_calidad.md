# Reporte de calidad: ventas de EnerAndes (hoja 2023)

- Filas en bronce: 1,114
- Filas en plata: 1,064
- Filas en cuarentena: 16

| # | Problema | Regla aplicada | Antes | Despues |
|---|---|---|---|---|
| 1 | Encabezado guardado como una fila | Usarlo como nombres de columna | 1 | 0 |
| 2 | Filas de totales | Eliminarlas | 1 | 0 |
| 3 | Filas duplicadas | Dejar una sola copia | 32 | 0 |
| 4 | Segmento escrito de varias formas | Unificar a 3 valores | 6 | 3 |
| 5 | Segmento vacio | Marcarlo como 'No informado' | 14 | 0 |
| 6 | Tipo de compra escrito de varias formas | Unificar a Bolsa y Contrato | 4 | 2 |
| 7 | Municipio escrito de varias formas | Unificar con el codigo DIVIPOLA | 31 | 15 |
| 8 | Energia vacia o negativa | Pasar la fila a cuarentena | 16 | 0 |
| 9 | Valor facturado vacio | Dejarlo vacio y documentarlo | 7 | 7 |
