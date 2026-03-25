try:
    import win32print
except ImportError:
    print("PYWIN32 NAO ESTA INSTALADO. INSTALE COM: PIP INSTALL PYWIN32")
    raise SystemExit(1)


flags = win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS
printers = win32print.EnumPrinters(flags)

if not printers:
    print("NENHUMA IMPRESSORA ENCONTRADA.")
    raise SystemExit(0)

for _, _, nome, _ in printers:
    print(nome)
