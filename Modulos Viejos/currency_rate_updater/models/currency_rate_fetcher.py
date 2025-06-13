import requests
from bs4 import BeautifulSoup
from datetime import datetime

def obtener_tasa_bcv():
    url_bcv = "https://www.bcv.org.ve/"
    try:
        response = requests.get(url_bcv, verify=False)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        dolar_div = soup.find('div', {'id': 'dolar'})
        if dolar_div:
            precio_elemento = dolar_div.find('strong')
            if precio_elemento:
                tasa = float(precio_elemento.text.strip().replace(',', '.'))
                fecha_actual = datetime.now().strftime("%Y-%m-%d")
                return tasa, fecha_actual
    except requests.exceptions.RequestException as e:
        return None, None
