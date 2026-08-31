# -*- coding: utf-8 -*-
"""Cruza las subcategorias prioritarias del reporte de boosteos de busqueda
(especialmente las de Fiestas Patrias) contra merged_full.csv para encontrar
CODIGOS DE ITEM concretos a promocionar en septiembre."""
import pandas as pd

df = pd.read_csv('merged_full.csv')

# Subcategorias senaladas como prioridad Alta/Media en el reporte de boosteos,
# marcando cuales son Fiestas Patrias (FP) segun ese reporte.
TARGET_SUBCATS = {
    ' MAYONESA (INDIVIDUAL)': ('46 - Mayonesa (boost search)', True),
    ' CAFE. SOLUBLE': ('41 - Nescafe/Cafe (boost search)', False),
    ' LACTEOS CULINARIOS': ('41 - Media crema/Carnation/Clavel/Lechera (FP guisos)', True),
    ' MEZCLAS DE ESPECIAS Y SAZONADORES': ('49 - Maggi/Knorr (FP guisos)', True),
    ' SALSAS PARA LA MESA': ('46 - Salsa inglesa (FP)', True),
    ' LECHE. ENTERA': ('41 - Leche entera (boost search)', False),
    ' CEREAL': ('41 - Cereal (FP)', True),
    ' UNTABLES': ('41 - Nutella (boost search)', False),
    ' CAFE. SUSTITUTO DE CREMA': ('41 - Coffee-Mate (boost search)', False),
    ' TOMATE': ('49 - Pure de tomate (FP mole/guisos)', True),
    ' CALDOS. POLLO': ('49 - Caldo de pollo (FP pozole)', True),
    ' SALSAS PARA COCINAR': ('46 - Salsa (FP)', True),
    ' MOLE': ('46 - Mole (FP ALTA prioridad)', True),
    ' ACEITE (INDIVIDUAL)': ('46 - Aceite (FP)', True),
    ' GALLETAS': ('68 - Galletas/Oreo/Saladitas (boost search)', False),
    ' EDULCORANTES': ('41 - Splenda (boost search)', False),
    ' MODIFICADORES DE LECHE': ('41 - Nesquik (boost search)', False),
}

sub = df[df['Sub_Cat_Desc'].isin(TARGET_SUBCATS.keys())].copy()
sub['Boost_Motivo'] = sub['Sub_Cat_Desc'].map(lambda s: TARGET_SUBCATS[s][0])
sub['Fiestas_Patrias'] = sub['Sub_Cat_Desc'].map(lambda s: TARGET_SUBCATS[s][1])

# Oportunidad = alto volumen en Piso pero bajo share .com (demanda fisica probada,
# poca conversion online) -- el perfil ideal para "buscar promocionar" via boost
# de busqueda interna + oferta.
sub['Share_Com_MTD_calc'] = sub['Com_Pesos_MTD'] / (sub['Com_Pesos_MTD'] + sub['Piso_Pesos_MTD'])

print("=== Total items en subcats objetivo:", len(sub), "===\n")

print("=== TOP 20 oportunidad (alto Piso, bajo share .com, subcats Fiestas Patrias) ===")
fp = sub[sub['Fiestas_Patrias']].copy()
fp_top = fp[(fp['Piso_Pesos_MTD'] > 200000) & (fp['Share_Com_MTD_calc'] < 0.08)].sort_values('Piso_Pesos_MTD', ascending=False).head(20)
cols = ['Item_Nbr', 'Item_Desc_1', 'Sub_Cat_Desc', 'Boost_Motivo', 'Piso_Pesos_MTD', 'Com_Pesos_MTD',
        'Share_Com_MTD_calc', 'Crecimiento_Com_Pesos_MTD', 'Crecimiento_Com_Pesos_L7D',
        'En_Parrilla', 'Promo_Vigente', 'Semaforo_OH']
print(fp_top[cols].to_string(index=False))

print("\n\n=== De esos, cuales YA estan en parrilla + promo vigente (listos, solo hay que boostear busqueda) ===")
ready = fp_top[fp_top['En_Parrilla'] & fp_top['Promo_Vigente']]
print(ready[cols].to_string(index=False) if len(ready) else "Ninguno de los top 20")

print("\n\n=== Universo completo: items FP en parrilla+promo vigente (accionables ya armados) ===")
fp_accionables = fp[(fp['En_Parrilla']) & (fp['Promo_Vigente'])].sort_values('Piso_Pesos_MTD', ascending=False)
print(fp_accionables[cols].to_string(index=False) if len(fp_accionables) else "Ninguno")

fp_top.to_csv('sept_boost_oportunidad_fp.csv', index=False, encoding='utf-8-sig')
fp_accionables.to_csv('sept_boost_accionables_listos.csv', index=False, encoding='utf-8-sig')
sub.to_csv('sept_boost_universo_completo.csv', index=False, encoding='utf-8-sig')
