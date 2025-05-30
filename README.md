See [description in English](#vk-cloud-vision-for-home-assistant) below 👇
<br>
<br>

# VK Cloud Vision для Home Assistant

[![Добавить репозиторий в HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=black-roland&repository=homeassistant-vkcloud-vision&category=integration)
[![Настроить интеграцию](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=vkcloud_vision)

Интеграция добавляет поддержку облачного распознавания объектов и текста через сервис VK Cloud Vision. Используйте возможности компьютерного зрения для создания автоматизаций на основе анализа изображений с камер видеонаблюдения.

## Возможности

- **Распознавание объектов** (людей, животных) и **автомобильных номеров**.
- **Распознавание текста** (OCR): например, надписей на автомобилях.
- Сохранение стоп-кадров с разметкой обнаруженных объектов.
- Blueprints для реализации распространённых сценариев.

VK Cloud Vision — это облачный сервис, плата за который взимается в соответствии с [тарифами](https://cloud.vk.com/docs/ru/ml/vision/tariffication). При первой регистрации можно получить [приветственные бонусы](https://cloud.vk.com/bonus/).

## Установка и настройка

### Подготовка

1. Зарегистрируйтесь в [VK Cloud](https://cloud.vk.com/app/signup/).
3. Создайте новый ключ в разделе «[Доступ через идентификатор клиента и секретный ключ](https://msk.cloud.vk.com/app/services/machinelearning/vision/access/)».
4. Сохраните полученные данные:
   - Идентификатор клиента (Client ID);
   - Секретный ключ (Client Secret).

### Установка

1. [Скачайте интеграцию](https://my.home-assistant.io/redirect/hacs_repository/?owner=black-roland&repository=homeassistant-vkcloud-vision&category=integration) через HACS.
2. Перезапустите Home Assistant.
3. Перейдите в **Настройки → Устройства и службы → Добавить интеграцию** или используйте [кнопку настройки](https://my.home-assistant.io/redirect/config_flow_start/?domain=vkcloud_vision).
4. Введите **Идентификатор клиента** и **Секретный ключ**, полученные в личном кабинете VK Cloud.

## Готовые автоматизации

Для типовых задач доступны готовые blueprints:

### Охранная сигнализация с облачным распознаванием объектов

[![Импорт blueprint](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fyaml.mansmarthome.info%2Froland%2F84cc0d91a7dd4517be28b3ee53f3a6b3%2Fdownload%2FHEAD%2Fobject_detection_triggered_alarm.yaml)

Активирует сигнализацию при обнаружении людей или транспортных средств, игнорируя ложные срабатывания (например, движение веток или животных).

### Оповещение при обнаружении объектов

[![Импорт blueprint](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fyaml.mansmarthome.info%2Froland%2F84cc0d91a7dd4517be28b3ee53f3a6b3%2Fdownload%2FHEAD%2Fmotion_triggered_object_detection_notifications.yaml)

Отправляет push-уведомления при обнаружении заданных объектов с прикреплением стоп-кадра и списком распознанных объектов.

## Доступные сервисы

Интеграция предоставляет два действия для анализа изображений с камер:

### `vkcloud_vision.detect_objects`

Обнаруживает объекты, сцены или автомобильные номера на изображениях с камеры. Позволяет сохранять стоп-кадры с рамками вокруг обнаруженных объектов.

Параметры:

- **modes** (необязательное, по умолчанию `["multiobject"]`) — режимы распознавания. Доступные варианты:
  - `multiobject`: Искать на изображении мультиобъекты — объекты и все множество боксов всех найденных объектов.
  - `car_number`: Распознавание автомобильных номеров.
  - `object`: Искать на изображении объекты.
  - `object2`: Искать на изображении объекты (версия модели v2 — распознает объекты, принадлежащие большему количеству классов).
  - `scene`: Распознавание сцен.
  - `pedestrian`: Искать на изображении людей (более точно определяет множество боксов всех людей на изображении).
  - `selfie`: Определение селфи.
- **file_out** (необязательное): Путь для сохранения стоп-кадра с разметкой (например, `/config/www/vkcloud_vision_snapshot.jpg`).
- **num_snapshots** (необязательное, по умолчанию `1`): Количество стоп-кадров, снимаемых с камеры с интервалом в одну секунду для повышения точности распознавания.

Пример использования:

```yaml
action: vkcloud_vision.detect_objects
target:
  entity_id: camera.front_door
data:
  modes:
    - multiobject
    - car_number
  file_out: /config/www/vkcloud_vision_snapshot.jpg
```

### `vkcloud_vision.recognize_text`

Распознает текст на изображениях с камеры (например, надписи на автомобилях).

Параметры:

- **detailed** (необязательное, по умолчанию `false`): Если `true`, возвращает подробные результаты с координатами текста и оценкой достоверности.

Пример использования:

```yaml
action: vkcloud_vision.recognize_text
target:
  entity_id: camera.front_door
data:
  detailed: true
```

<!--
## Планы по развитию

В будущих версиях планируется добавить:

- **Автоматическое создание нескольких стоп-кадров** для повышения точности распознавания.
- **Подписи на русском языке** на стоп-кадрах с разметкой объектов (при наличии интереса и поддержки через донаты).
- **Распознавание лиц** с классификацией по признакам (возраст, пол, эмоции), если будет достаточная поддержка сообщества через донаты.
-->

## Поддержка автора

Если эта интеграция оказалась для вас полезна, подумайте о том, чтобы [угостить автора чашечкой кофе](https://mansmarthome.info/donate/#donationalerts). Ваша благодарность ценится!

## Уведомление

Данная интеграция является неофициальной и не связана с VK Cloud. VK Cloud Vision — это сервис, предоставляемый VK Cloud.

Данная интеграция не является официальным продуктом VK Cloud и не поддерживается VK.

---

# VK Cloud Vision for Home Assistant

[![Add repository to HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=black-roland&repository=homeassistant-vkcloud-vision&category=integration)
[![Configure Integration](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=vkcloud_vision)

This integration brings cloud-based object and text recognition to Home Assistant using the [VK Cloud Vision](https://cloud.vk.com/vision/) service. Leverage computer vision to create automations based on image analysis from surveillance cameras.

## Key Features

- **Object and license plate detection** using the `vkcloud_vision.detect_objects` action.
- **Text recognition** on images (e.g., vehicle inscriptions) using the `vkcloud_vision.recognize_text` action.
- Create automations based on image analysis from surveillance cameras.
- Save snapshots with annotations of detected objects.

## Installation and Setup

### Prerequisites

**Register with VK Cloud**:
- Sign up at [VK Cloud](https://cloud.vk.com/app/signup/).
- Activate the Vision service in the [dashboard](https://msk.cloud.vk.com/app/services/machinelearning/vision/access/).
- Generate access keys in the **AI API → Vision API** section:
  - **Client ID**.
  - **Client Secret**.
- Save the keys for integration setup.

### Installation

1. Open **HACS → Integrations**.
2. Click the three-dot menu in the top right and select **Custom repositories**.
3. Add the repository: `https://github.com/black-roland/homeassistant-vkcloud-vision`, select **Integration** as the category.
4. Find and install the **VK Cloud Vision** integration.
5. Restart Home Assistant.

### Configuration

1. Go to **Settings → Devices & Services → Add Integration** or use the [configuration button](https://my.home-assistant.io/redirect/config_flow_start/?domain=vkcloud_vision).
2. Enter the **Client ID** and **Client Secret** obtained from VK Cloud.
3. Save the configuration and restart Home Assistant if prompted.

## Donations

If this integration has been useful to you, consider [buying the author a coffee](https://www.donationalerts.com/r/mansmarthome). Your gratitude is appreciated!

## Notice

This is a community project, not affiliated with VK Cloud. VK Cloud Vision is a service provided by VK Cloud.

This integration is not an official VK Cloud product and is not supported by VK.
