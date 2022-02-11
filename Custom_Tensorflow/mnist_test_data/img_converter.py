import tensorflow as tf
from PIL import Image
image = Image.open('img_1.jpg')
image.show()
print(image.size)
print("IMG:",image)
#tf.image.convert_image_dtype(  image, dtype= tf.float32, saturate=False)
array = tf.keras.preprocessing.image.img_to_array(image)
print((array))
