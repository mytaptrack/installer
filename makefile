run:
	streamlit run mytaptrack_installer.py

build:
	docker build . -t mytaptrack/installer

publish:
	docker build . -t mytaptrack/installer
	docker push mytaptrack/installer:latest

