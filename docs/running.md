---
layout: default
title: Running your application
---

# Running your application
Your application is packaged and run using Docker, and we use [Docker-Compose](https://docs.docker.com/compose/) to start your container.
This way it's very easy for you to add companion containers to your application like log collectors, metric collectors and so on.

The docker-compose process is handled by [systemd](https://www.freedesktop.org/wiki/Software/systemd/) so you don't have to worry about the process dying: systemd will recreate the process if something happens.

