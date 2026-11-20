"""Regiones (agrupación del Banco Mundial; América Latina = los 16 países hispanohablantes y lusófonos usados en todo el proyecto).
El Caribe no hispano y Puerto Rico quedan como grupo aparte y no entran en las pruebas entre regiones."""
LAT=['ARG','BOL','BRA','CHL','COL','CRI','DOM','ECU','GTM','HND','MEX','PAN','PER','PRY','SLV','URY']
R={'América Latina':LAT,
 'Norteamérica':['CAN','USA'],
 'Europa y Asia Central':'ALB ARM AUT AZE BEL BGR BIH CHE CYP CZE DEU DNK ESP EST FIN FRA GBR GEO GRC HRV HUN IRL ISL ITA KAZ KGZ LTU LUX LVA MDA MKD MLT NLD NOR POL PRT ROU SRB SVK SVN SWE TUR UKR UZB'.split(),
 'Asia Oriental y Pacífico':'AUS IDN JPN KHM KOR MNG MYS NZL PHL SGP THA TWN VNM'.split(),
 'Asia del Sur':'BGD IND LKA NPL PAK'.split(),
 'Oriente Medio y Norte de África':'ARE BHR DZA EGY IRQ ISR JOR KWT LBN MAR OMN PSE QAT SAU TUN'.split(),
 'África Subsahariana':'AGO BEN BFA BWA CIV CMR COG GHA KEN MDG MOZ MUS NAM NGA RWA SEN TGO TZA UGA ZAF ZMB ZWE'.split(),
 'Caribe (fuera de pruebas)':'HTI JAM TTO PRI'.split()}
REGION={c:r for r,cs in R.items() for c in cs}
