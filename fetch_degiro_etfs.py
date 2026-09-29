import getpass
import time
import pandas as pd
from degiro_connector.trading.api import API as TradingAPI
from degiro_connector.trading.models.credentials import Credentials
from degiro_connector.trading.models.product_search import LookupRequest
import os

def main():
    print("========================================")
    print(" DEGIRO ETF Exporter (Met automatische 2FA Pauze)")
    print("========================================")
    print("Vul je inloggegevens in. Deze worden lokaal gehouden en nergens opgeslagen.")
    
    username = input("Gebruikersnaam: ")
    password = getpass.getpass("Wachtwoord: ")
    
    credentials = Credentials(
        int_account=None,
        username=username,
        password=password,
        totp_secret=None
    )

    trading_api = TradingAPI(credentials=credentials)
    
    # Patch session to capture response text
    captured_in_app_token = None
    original_send = trading_api.session_storage.session.send
    def patched_send(*args, **kwargs):
        nonlocal captured_in_app_token
        res = original_send(*args, **kwargs)
        if res.status_code != 200:
            try:
                data = res.json()
                if "inAppToken" in data:
                    captured_in_app_token = data["inAppToken"]
            except:
                pass
        return res
        
    trading_api.session_storage.session.send = patched_send
    
    print("\nInloggen op DEGIRO...")
    try:
        trading_api.connect()
        print("Succesvol ingelogd!")
    except Exception as e:
        if captured_in_app_token:
            print("\n=======================================================")
            print("   PAUZE: 2FA GOEDKEURING VEREIST VIA DEGIRO APP!")
            print("=======================================================")
            print("1. Open NU de DEGIRO app op je smartphone.")
            print("2. Tik op 'Ja' om deze inlogpoging goed te keuren.")
            print("-> Ik wacht maximaal 60 seconden...")
            print("=======================================================\n")
            
            credentials.in_app_token = captured_in_app_token
            
            success = False
            for i in range(12):
                time.sleep(5)
                try:
                    trading_api.connect()
                    success = True
                    break
                except Exception as loop_e:
                    # Keep trying
                    pass
            
            if success:
                print("=> Succesvol ingelogd na goedkeuring op telefoon!")
            else:
                print("=> Inloggen niet gelukt. De tijd is waarschijnlijk verstreken of je hebt niet op Ja gedrukt.")
                return
        else:
            print(f"Fout bij inloggen: {e}")
            return

    offset = 0
    limit = 500
    all_etfs = []
    print("\nETF's aan het ophalen. Dit duurt even...")

    while True:
        request = LookupRequest(
            search_text="",
            offset=offset,
            limit=limit,
            product_type_id=131
        )
        
        try:
            response = trading_api.product_search(
                product_request=request,
                raw=True
            )
        except Exception as e:
            print(f"Fout bij het ophalen van de data: {e}")
            break
        
        products = []
        if isinstance(response, dict) and "products" in response:
            products = response["products"]
        elif isinstance(response, list):
            products = response

        if not products:
            break
            
        all_etfs.extend(products)
        print(f"{len(all_etfs)} ETF's opgehaald...")
        
        if len(products) < limit:
            break
            
        offset += limit
        
    if all_etfs:
        df = pd.DataFrame(all_etfs)
        filename = "degiro_etfs.csv"
        if os.path.exists(filename):
            os.remove(filename)
            
        df.to_csv(filename, index=False)
        print(f"\nKlaar! {len(all_etfs)} ETF's weggeschreven naar '{filename}'.")
    else:
        print("\nGeen ETF's gevonden.")

if __name__ == "__main__":
    main()
