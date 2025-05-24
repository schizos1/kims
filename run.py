from app import create_app

# 애플리케이션 팩토리를 호출하여 앱 인스턴스 생성
app = create_app()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')