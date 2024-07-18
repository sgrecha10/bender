from PIL import Image, ImageDraw
from django.http.response import HttpResponse
from django.views import View


class CandleView(View):
    def get(self, request):
        # создаем картинку, пишем в неё текст и сохраняем
        text = "Abracadabra :)"  # готовим текст
        color = (0, 100, 100)  # создаем цвет
        img = Image.new('RGB', (300, 300), color)  # создаем изображение
        imgDrawer = ImageDraw.Draw(img)
        imgDrawer.text((10, 20), text)  # пишем на изображении наш текст
        response = HttpResponse(content_type="image/png")
        img.save(response, "png")

        return response
