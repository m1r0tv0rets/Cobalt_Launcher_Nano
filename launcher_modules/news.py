if command == "новости":
  url_news = "https://raw.githubusercontent.com/m1r0tv0rets/Cobalt_Launcher_Nano/main/news.txt"
  req = urllib.request.Request(url_news, headers={'User-Agent': 'Mozilla'})
   
  try:
   with urllib.request.urlopen(req) as r:
    print(r.read().decode('utf-8'))
  
  except Exception as e:
   print(f"Ошибка: {e}") 
  finally:
   urllib.request.urlcleanup()