# VK Cloud Vision для Home Assistant

[![Добавить репозиторий в HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=black-roland&repository=homeassistant-vkcloud-vision&category=integration)
[![Настроить интеграцию](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=vkcloud_vision)

Интеграция добавляет поддержку облачного распознавания объектов через сервис [VK Cloud Vision](https://cloud.vk.com/vision/) в Home Assistant.

Сервис работает через облако VK Cloud. При [первой регистрации](https://cloud.vk.com/app/signup/) доступны приветственные бонусы.

> [!IMPORTANT]
> **Интеграция в активной разработке**, функционал может меняться. Актуальные новости о прогрессе разработки можно найти в [Telegram-канале](https://t.me/mansmarthome).

## Возможности

- Анализ изображений с камер в реальном времени
- Создание автоматизаций на основе распознанных объектов
- Модерация пользовательского контента
- Получение метаданных изображений
- Поддержка всех функций API VK Vision

## Примеры использования

[![Open your Home Assistant instance and show the blueprint import dialog with a specific blueprint pre-filled.](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fyaml.mansmarthome.info%2Froland%2F84cc0d91a7dd4517be28b3ee53f3a6b3%2Fraw%2FHEAD%2Fsimple_object_identification.yaml)

## Подготовка

1. Зарегистрируйтесь в [VK Cloud](https://cloud.vk.com/app/signup/)
2. Активируйте сервис Vision в [личном кабинете](https://msk.cloud.vk.com/app/services/machinelearning/vision/access/)
3. Создайте новый ключ доступа в разделе "Управление доступом"
4. Сохраните полученные:
   - Идентификатор клиента (Client ID)
   - Секретный ключ (Client Secret)

## Настройка

1. Добавьте репозиторий в HACS
2. Установите интеграцию через интерфейс Home Assistant
3. Введите полученные учетные данные при настройке
4. Перезагрузите Home Assistant

Тарифы на использование сервиса: [cloud.vk.com/docs/ru/ml/vision/tariffication](https://cloud.vk.com/docs/ru/ml/vision/tariffication)

## Поддержка проекта
Если проект полезен для вас, поддержите разработку:
[Пожертвовать через DonationAlerts](https://mansmarthome.info/donate#donationalerts)

## Уведомление

Данная интеграция является неофициальной и не связана с VK Cloud. VK Cloud Vision — это сервис, предоставляемый VK Cloud.

Данная интеграция не является официальным продуктом VK Cloud и не поддерживается VK.

---

# VK Cloud Vision for Home Assistant

[![Add repository to HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=black-roland&repository=homeassistant-vkcloud-vision&category=integration)
[![Configure Integration](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=vkcloud_vision)

Integration for cloud-based object recognition using [VK Cloud Vision](https://cloud.vk.com/vision/) service.

## Key Features

- Object and scene recognition
- Text recognition (OCR/STR)
- Face detection and emotion analysis
- NSFW content moderation
- Document processing

## Setup

1. Register at [VK Cloud](https://cloud.vk.com/app/signup/)
2. Activate Vision service in [dashboard](https://msk.cloud.vk.com/app/services/machinelearning/vision/access/)
3. Create API access keys
4. Install integration via HACS

Pricing: [cloud.vk.com/docs/ru/ml/vision/tariffication](https://cloud.vk.com/docs/ru/ml/vision/tariffication)

## Support

[Donate via DonationAlerts](https://mansmarthome.info/donate#donationalerts)

## Notice

This is a community project, not affiliated with VK Cloud. VK Cloud Vision is a service provided by VK Cloud.

This integration is not an official VK Cloud product and is not supported by VK.
