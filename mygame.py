import openai
from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
from dotenv import load_dotenv
import os
from langchain_openai import ChatOpenAI
from textblob import TextBlob
import random

# .env 파일 로드
load_dotenv()

# OpenAI API 키 설정
openai.api_key = os.getenv('OPENAI_API_KEY')

# langchain ChatOpenAI 인스턴스 생성
chat = ChatOpenAI(model_name='gpt-3.5-turbo')

# Ursina 게임 엔진을 초기화합니다.
app = Ursina()

# 하늘 텍스처를 추가합니다.
Sky(texture="sky_sunset")

# 1인칭 플레이어 컨트롤러를 추가합니다.
player = FirstPersonController()
player.cursor.enabled = False  # 커서를 숨김

# 강아지 모델을 추가합니다.
dog = Entity(
    model='dog.obj',  # 강아지 모델 파일 경로
    texture='Dog_dif.jpg',  # 강아지 텍스처 파일 경로
    scale=(0.05, 0.05, 0.05),
    position=(10, 0.3, 10),
    rotation=(-90, 0, 0)  # 초기 회전 값을 조정하여 똑바로 앉도록 함
)

dog_is_happy = False
dog_follow_player = False
dog_health = 3
game_over = False

# 채팅 메시지를 표시할 리스트
chat_messages = []
MAX_CHAT_MESSAGES = 2  # 최대 메시지 수

# 채팅 UI 구성
chat_input = InputField(default_value='', position=(-0.5, -0.45), enabled=False, visible=False)
chat_input.scale = (0.6, 0.05)  # scale을 별도로 설정
chat_display = Text(text='', position=(-0.5, -0.35), scale=1, background=True)

# 감성 분석 결과를 표시할 텍스트 추가
sentiment_text = Text(text='', position=(-0.5, 0.45), scale=1.5, color=color.black)
cumulative_sentiment_text = Text(text='Total Sentiment: 0.00', position=(-0.5, 0.40), scale=1.5, color=color.black)

# 누적 감정 점수 변수
cumulative_sentiment = 0.0

# 이모지 텍스처를 표시할 이미지 추가 (초기 설정을 Neutral로 변경)
emoji_display = Entity(parent=camera.ui, model='quad', texture='Neutral.png', scale=(0.1, 0.1), position=(0.4, 0.4))

# "Dog State" 텍스트를 이모지 위에 추가
dog_state_text = Text(text='Dog State', position=(0.33, 0.5), scale=1.5, color=color.black)

# 체력을 표시할 하트 이미지 추가
hearts = [Entity(parent=camera.ui, model='quad', texture='heart.png', scale=(0.06, 0.06), position=(-0.7 + 0.07 * i, 0.45)) for i in range(3)]

def update():
    if game_over:
        return

    if chat_input.enabled:
        player.enabled = False
        return
    player.enabled = True

    # 플레이어의 이동을 벽으로 제한
    check_player_wall_collision()

    if dog_follow_player:
        # 강아지가 플레이어를 따라오도록 설정
        follow_player()
    else:
        # 강아지가 무작위로 돌아다니도록 설정
        random_walk()

    # 강아지가 한 바퀴 천천히 돌도록 설정
    if dog_is_happy:
        dog.rotation_y += time.dt * 100  # 회전 속도 조절 (값이 클수록 빨라짐)

def check_player_wall_collision():
    # 플레이어의 위치를 벽 내로 제한
    if player.x < -19:
        player.x = -19
    elif player.x > 19:
        player.x = 19
    if player.z < -19:
        player.z = -19
    elif player.z > 19:
        player.z = 19

def follow_player():
    if not dog_is_happy:
        # 강아지가 플레이어를 바라보게 회전
        dog.look_at(player.position)
        
        # 플레이어와 강아지 사이의 거리 계산
        distance = distance_to(player.position, dog.position)

        # 강아지가 플레이어를 따라오도록 위치 업데이트 (최소 거리 유지)
        min_distance = 7  # 최소 거리 설정
        if distance > min_distance:
            direction = (player.position - dog.position).normalized()
            dog.position += direction * time.dt * 2  # 따라오는 속도 조절

    # 강아지가 수평을 유지하도록 회전 보정
    dog.rotation_x = -90
    dog.rotation_z = 0

def random_walk():
    # 무작위로 이동 방향을 설정
    if random.random() < 0.01:  # 확률적으로 방향 변경
        dog.rotation_y += random.uniform(-90, 90)

    # 현재 방향으로 이동
    direction = Vec3(math.cos(math.radians(dog.rotation_y)), 0, math.sin(math.radians(dog.rotation_y)))
    new_position = dog.position + direction * time.dt

    # 이동 범위를 체크하여 벽을 넘어가지 않도록 함
    if -19 < new_position.x < 19 and -19 < new_position.z < 19:
        dog.position = new_position

    # 강아지가 수평을 유지하도록 회전 보정
    dog.rotation_x = -90
    dog.rotation_z = 0

def distance_to(p1, p2):
    return ((p1.x - p2.x) ** 2 + (p1.y - p2.y) ** 2 + (p1.z - p2.z) ** 2) ** 0.5

def analyze_sentiment(message):
    blob = TextBlob(message)
    return blob.sentiment.polarity

def handle_chat_response(message):
    sentiment = analyze_sentiment(message)
    if sentiment == 0.0:
        response = "Woof Woof!! Grr.."
    else:
        response = chat.predict(message)
        response = make_cute(response)
    return response.strip()

def make_cute(response):
    # 귀여운 강아지 말투로 변환
    cute_phrases = {
        #'I': 'Me',
        'you': 'yoo',
        'are': 'awre',
        'my': 'mah',
        '.': '!',
        '!': '!!',
        '?': '??'
    }
    for word, cute_word in cute_phrases.items():
        response = response.replace(word, cute_word)
    # R, L 소리를 W로 발음하도록 변환
    #response = response.replace('r', 'w').replace('l', 'w')
    #response = response.replace('R', 'W').replace('L', 'W')
    response += " Woof Woof!"
    return response

def submit_chat():
    global dog_is_happy, cumulative_sentiment, dog_follow_player, dog_health, game_over
    if game_over:
        return

    message = chat_input.text
    if message:
        chat_messages.append("User: " + message)
        response = handle_chat_response(message)
        chat_messages.append("Dog: " + response)

        if len(chat_messages) > MAX_CHAT_MESSAGES * 2:
            chat_messages.pop(0)
            chat_messages.pop(0)

        chat_input.text = ''
        update_chat_display()

        sentiment = analyze_sentiment(message)
        sentiment_text.text = f'Sentiment: {sentiment:.2f}'

        # 누적 감정 점수 업데이트 및 텍스트 표시
        cumulative_sentiment += sentiment
        cumulative_sentiment_text.text = f'Total Sentiment: {cumulative_sentiment:.2f}'

        dog_follow_player = True  # 채팅이 입력되면 플레이어를 따라오게 설정

        if cumulative_sentiment >= 1.0:
            sentiment_text.text += ' (Positive)'
            dog_is_happy = True
            dog.color = color.red
            dog.position = (dog.position[0], 0.3, dog.position[2])
            emoji_display.texture = 'smile.png'  # 긍정적인 감정일 때 웃는 이모지
        elif cumulative_sentiment <= -1.0:
            sentiment_text.text += ' (Negative)'
            dog_is_happy = False
            dog.color = color.blue
            dog.position = (dog.position[0], 0.3, dog.position[2])
            emoji_display.texture = 'sad.png'  # 부정적인 감정일 때 우는 이모지
            if sentiment < 0:
                dog_health -= 1
                update_hearts()
                if dog_health == 0:
                    emoji_display.texture = 'angry.png'  # 체력이 다 깎이면 화내는 이모지
                    chat_messages.append("Dog: Grrr!! Woof Woof!")
                    show_game_over_screen()
                    game_over = True
        else:
            sentiment_text.text += ' (Neutral)'
            dog.color = color.black
            dog_is_happy = False
            emoji_display.texture = 'Neutral.png'  # 중립일 때 이모지

    chat_input.enabled = False
    chat_input.visible = False
    chat_input.text = ''  # 입력 필드 초기화
    mouse.locked = True  # 마우스 커서 고정

def show_game_over_screen():
    global game_over_text
    game_over_text = Text(text='Game Over', origin=(0, 0), scale=3, color=color.red)
    game_over_text.background = True

def update_hearts():
    for i in range(3):
        if i < dog_health:
            hearts[i].visible = True
        else:
            hearts[i].visible = False

def update_chat_display():
    chat_display.text = '\n'.join(chat_messages[-MAX_CHAT_MESSAGES * 2:])  # 최신 메시지 표시

def input(key):
    global game_over
    if key == 'escape':
        application.quit()  # ESC 키를 누르면 게임 종료

    if game_over:
        if key == 'escape':
            application.quit()
        return

    if chat_input.enabled:
        if key == 'enter':
            submit_chat()
        else:
            return  # 채팅 입력 필드가 활성화되어 있을 때는 다른 입력을 무시
    else:
        if key == 'enter':
            chat_input.enabled = True
            chat_input.visible = True
            chat_input.active = True
            mouse.locked = False  # 마우스 커서 해제

# 바닥 블록을 생성합니다.
blocks = []
for i in range(-20, 21):
    for j in range(-20, 21):
        block = Button(
            color=color.white,
            model='cube',
            position=(j, 0, i),
            texture='gree.jpg',
            parent=scene,
            origin_y=0.5)
        blocks.append(block)

# 벽을 생성합니다.
wall_thickness = 1
wall_height = 3
# 좌측 벽
wall_left = Entity(model='cube', texture='wall.png', scale=(wall_thickness, wall_height, 40), position=(-20.5, wall_height / 2, 0))
# 우측 벽
wall_right = Entity(model='cube', texture='wall.png', scale=(wall_thickness, wall_height, 40), position=(20.5, wall_height / 2, 0))
# 상단 벽
wall_top = Entity(model='cube', texture='wall.png', scale=(40, wall_height, wall_thickness), position=(0, wall_height / 2, -20.5))
# 하단 벽
wall_bottom = Entity(model='cube', texture='wall.png', scale=(40, wall_height, wall_thickness), position=(0, wall_height / 2, 20.5))

# 텍스처 타일링 설정
wall_left.texture_scale = (20, 1)
wall_right.texture_scale = (20, 1)
wall_top.texture_scale = (20, 1)
wall_bottom.texture_scale = (20, 1)


# 벽에 충돌 속성을 추가하여 플레이어가 벽을 통과하지 못하도록 설정
wall_left.collider = 'box'
wall_right.collider = 'box'
wall_top.collider = 'box'
wall_bottom.collider = 'box'

# 게임을 실행합니다.
app.run()
