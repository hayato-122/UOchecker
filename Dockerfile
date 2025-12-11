FROM python:3.13.9

RUN useradd -m -u 1000 user

WORKDIR /app
RUN chown user:user /app

USER user

ENV PATH="/home/user/.local/bin:$PATH"

COPY --chown=user requirements.txt .

RUN pip install --no-cache-dir --upgrade -r requirements.txt

COPY --chown=user . .

RUN STREAMLIT_PATH=$(python -c "import streamlit; print(streamlit.__file__)") && \
    INDEX_PATH=$(dirname $STREAMLIT_PATH)/static/index.html && \
    sed -i 's/lang="en"/lang="ja" class="notranslate" translate="no"/g' $INDEX_PATH

CMD ["streamlit", "run", "frontend.py", "--server.address=0.0.0.0", "--server.port=7860"]