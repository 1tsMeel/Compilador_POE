import basic

while True:
    # Este archivo simulará una consola
	text = input('introduce > ')
	if text.strip() == "": continue
	result, error = basic.run('<stdin>', text) # Se ejecuta el comando con <stdin>

	# Si hay error se muestra en pantalla, si no se muestra el resultado
	if error:
		print(error.as_string())
	elif result:
		if len(result.elements) == 1:
			print(repr(result.elements[0]))
		else:
			print(repr(result))
   
   
   # Código para debug descartado
	""" source_code = """
	#VAR x = 10
	#PRINT(x)
	"""
	output, error = basic.generate_object_code("<stdin>", source_code, "codigo_objeto.txt")
	if error:
		print("Error:", error)
	else:
		print(output) """