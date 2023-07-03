with open("tmp", 'r') as tmp_file:
    text = tmp_file.read()
text = text.split("\n") 
first_line = text[0]
first_line = first_line.split(' ')
first_line[2] = "model_name[]"

text[0] = ' '.join(first_line)
text = '\n'.join(text)
with open("tmp", 'w') as tmp_file:
    text = tmp_file.write(text)