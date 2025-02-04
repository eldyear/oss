import os
import datetime
from django.db import models
from django.utils.text import get_valid_filename
from django.utils import timezone
import logging
from django.core.exceptions import ValidationError

logger = logging.getLogger(__name__)

STATUS_CHOICES = (
    ('Регистрация','Регистрация'),('Посадка','Посадка'),('Отправлен','Отправлен'),(' ', ' '),
    ('По готовности','По готовности'),('Задержан','Задержан'),('Отменен','Отменен'), ('По расписанию','По расписанию'), ('Выполнен','Выполнен')
)

DIRECTION = (
    ('dep', 'Вылет'),
    ('arr', 'Прилет')
)

class Status(models.Model):
    status_id = models.CharField(max_length=2, verbose_name="ID статуса", blank=True, null=True, unique=True)
    name_ru = models.CharField(max_length=50, verbose_name="Статус на русском", blank=True, null=True, unique=True)
    name_ky = models.CharField(max_length=50, verbose_name="Статус на кыргызском", blank=True, null=True, unique=True)
    name_en = models.CharField(max_length=50, verbose_name="Статус на английском", blank=True, null=True, unique=True)

    def __str__(self):
        return "{}".format(self.name_ru)

    class Meta:
        db_table = 'Status'
        verbose_name = "Статус"
        verbose_name_plural = "Статусы"


class FlightNumber(models.Model):
    # flight_code = models.CharField(max_length=3,verbose_name="Код авиакомпании ", unique=True)
    flights = models.CharField(max_length=10,verbose_name="№ Рейса ", unique=True)
    def __str__(self):
        return "{}".format(self.flights)

    class Meta:
        db_table = 'FlightNumber'
        verbose_name = "№ Рейса"
        verbose_name_plural = "№ Рейсов"

class Cities(models.Model):
    city_name_ru = models.CharField(max_length=50, verbose_name="Город на русском")
    city_name_ky = models.CharField(max_length=50, verbose_name="Город на кыргызском")
    city_name_en = models.CharField(max_length=50, verbose_name="Город на английском")
    iata_code = models.CharField(max_length=3, verbose_name="IATA код")
    icao_code = models.CharField(max_length=4, verbose_name="ICAO код", blank=True)
    def __str__(self):
        return "{}".format(self.city_name_ru)

    class Meta:
        db_table = 'City'
        verbose_name = "Город"
        verbose_name_plural = "Города"


class Stoiki(models.Model):
    stoiki = models.CharField(max_length=2,verbose_name="Стойка № ", unique=True)
    def __str__(self):
        return "Стойка - {}".format(self.stoiki)
    def get_number(self):
        return self.stoiki

    class Meta:
        db_table = 'Stoiki'
        verbose_name = "№ Стойки"
        verbose_name_plural = "№ Стоек"

class Gates(models.Model):
    gate = models.CharField(max_length=2,verbose_name="Gate № ", unique=True)
    def __str__(self):
        return "Gate - {}".format(self.gate)
    def get_number(self):
        return self.gate

    class Meta:
        db_table = 'Gates'
        verbose_name = "Gate:"
        verbose_name_plural = "Gates:"

class Airline(models.Model):
    name = models.CharField(max_length=20, verbose_name="Авиакомпания", blank=True, unique=True)
    code = models.CharField(max_length=3, verbose_name="Код авиакомпании", blank=True, unique=True)
    logo = models.ImageField(upload_to='airline_logos/', verbose_name="Логотип", blank=True)
    svg_logo = models.FileField(upload_to='airline_logos/svg/', verbose_name="SVG логотип", blank=True)

    def save(self, *args, **kwargs):
        if Airline.objects.filter(code=self.code).exclude(pk=self.pk).exists():
            raise ValidationError(f"Авиакомпания с кодом '{self.code}' уже существует.")
        if self.svg_logo:
            # Получаем расширение файла
            svg_ext = self.svg_logo.name.split('.')[-1]
            # Создаем новое имя файла, используя поле code
            svg_new_filename = f"{self.code}.{svg_ext}"
            # Удаляем недопустимые символы из имени файла
            svg_new_filename = get_valid_filename(svg_new_filename)
            # Устанавливаем новое имя файла
            self.svg_logo.name = svg_new_filename
        
        super(Airline, self).save(*args, **kwargs)

    def __str__(self):
        return "{}".format(self.name)

    class Meta:
        db_table = 'Airline'
        verbose_name = "Авиакомпания"
        verbose_name_plural = "Авиакомпании"

from django.utils import timezone

class InfTablo(models.Model):
    direction = models.CharField(max_length=3, choices=DIRECTION)
    airline = models.ForeignKey(
        Airline,
        on_delete=models.CASCADE,
        verbose_name="Авиакомпания *",
        related_name='inftablo_airline'
    )
    flight = models.ForeignKey(
        FlightNumber,
        on_delete=models.CASCADE,
        verbose_name="Рейс № *",
    )
    destination = models.ForeignKey(
        Cities,
        on_delete=models.CASCADE,
        verbose_name="Пункт назначение *",
    )
    date1 = models.DateField("Дата плановая*", null=True)
    time1 = models.TimeField("Время плановая*", null=True)
    arr_time = models.TimeField("Время прибытия", blank=True, null=True)
    last_date = models.DateField("Дата (факт)", blank=True, null=True)
    last_time = models.TimeField("Время (факт)", blank=True, null=True)
    status = models.ForeignKey(
        Status,
        on_delete=models.CASCADE,
        verbose_name="Статус",
        blank=True,
        null=True
    )
    stoika = models.ManyToManyField(
        Stoiki,
        related_name='CheckDesk',
        verbose_name="Табло №",
        blank=True
    )
    
    gate = models.ManyToManyField(
        Gates,
        related_name='Gate',
        verbose_name="Gate:",
        blank=True
    )

    def __str__(self):
        return "{}".format(self.destination)
    
    def update_status_if_departed(self):
        """Автоматически устанавливает статус 'Отправлен' при совпадении current_time с last_time."""
        current_time = timezone.now().time()  # Текущее время
        
        # Находим статус "Отправлен" в базе данных
        sent_status = Status.objects.filter(name_ru="Отправлен").first()
          # Выводим в консоль терминала
        if sent_status:
            logger.info(f"Получен статус 'Отправлен': {sent_status}")
        else:
            logger.warning("Статус 'Отправлен' не найден в базе данных")

        # Проверяем, что поле last_time установлено и текущий статус не равен "Отправлен"
        if self.last_time and self.status != sent_status:
            # Если текущее время совпадает с last_time, устанавливаем статус "Отправлен"
            if current_time == self.last_time and sent_status:
                self.status = sent_status

    def save(self, *args, **kwargs):
        # Обновляем статус на "Отправлен", если время совпадает
        self.update_status_if_departed()
        super().save(*args, **kwargs)

    class Meta:
        db_table = "InfTablo"
        verbose_name = '"Суточный план"'
        verbose_name_plural = "Суточный план"

class FlightForTemplate(models.Model):
    airline = models.ForeignKey(
        Airline,
        on_delete=models.CASCADE,
        verbose_name="Авиакомпания *",
        related_name='template_airline',
        default=1
    )
    flight = models.ForeignKey(
        FlightNumber,
        on_delete=models.CASCADE,
        verbose_name="Рейс № *",
        related_name='template_flight',
        default=1
    )
    destination = models.ForeignKey(
        Cities,
        on_delete=models.CASCADE,
        verbose_name="Пункт назначение *",
        related_name='template_destination',
        default=1
    )
    
    

    def __str__(self):
        return "{}".format(self.flight)

    class Meta:
        verbose_name = "Информация о рейсе"
        verbose_name_plural = "Информации о рейсах"

class FlightTemplate(models.Model):
    """
    Модель для хранения шаблонов рейсов.
    """
    direction = models.CharField("Направление *", max_length=10, default="", choices=DIRECTION)
    season_start = models.DateField("Начало сезона")
    season_end = models.DateField("Конец сезона")
    weekdays = models.CharField(
        "Дни вылета", 
        max_length=20, 
        help_text="Введите дни недели через запятую, например: 1,3,5 для понедельника, среды и пятницы"
    )
    period_start = models.DateField("Начало периода рейса")
    period_end = models.DateField("Конец периода рейса")
    time = models.TimeField("Время плановая*", null=True)

    flight = models.ForeignKey(
        FlightForTemplate,  # Связываем с моделью InfTablo
        on_delete=models.CASCADE,  # Удаление рейса приведёт к удалению всех шаблонов
        verbose_name="Рейс", 
        related_name="flight_templates"  # Обратная связь: InfTablo.flight_templates.all()
    )


    def __str__(self):
        return f"Шаблон рейса {self.flight.flight} ({self.season_start} - {self.season_end})"

    class Meta:
        verbose_name = "Шаблон рейса"
        verbose_name_plural = "Шаблоны рейсов"

