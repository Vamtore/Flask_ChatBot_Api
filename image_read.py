import easyocr

reader = easyocr.Reader(['en'])

results = reader.readtext('test2.png')

text = ''
for result in results:
    text+= result[1]+''

print(text)