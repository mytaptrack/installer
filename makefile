run:
	streamlit run mytaptrack_installer.py

fullrun:
	. .venv/bin/activate && streamlit run mytaptrack_installer.py

build:
	docker build . -t mytaptrack/installer

publish:
	docker build --platform=linux/amd64 -t mytaptrack/installer .
	docker push mytaptrack/installer:latest
