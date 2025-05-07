# If you need Python 3 and the GitHub CLI, then use:
FROM cicirello/pyaction:4

# If all you need is Python 3, use:
# FROM cicirello/pyaction-lite:3

# If Python 3 + git is sufficient, then use:
# FROM cicirello/pyaction:3

# To pull from the GitHub Container Registry instead, use one of these:
# FROM ghcr.io/cicirello/pyaction-lite:3
# FROM ghcr.io/cicirello/pyaction:4
# FROM ghcr.io/cicirello/pyaction:3

# RUN ls
# RUN git rev-parse --is-inside-work-tree
# RUN git config --global --add safe.directory /github/workspace

COPY requirements.txt /requirements.txt
RUN pip install --no-cache-dir -r /requirements.txt
RUN mkdir -p /github/workspace/comments
COPY scripts/language_images.json /scripts/language_images.json
COPY scripts/template.yml /scripts/template.yml
COPY localization_differ.py /localization_differ.py
COPY entrypoint.py /entrypoint.py
ENTRYPOINT ["/entrypoint.py"]

RUN LS /github/workspace
