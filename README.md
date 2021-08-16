# Yatube
> A small social network for authors.

### Description

It is a small social network where authors can write posts and attach images to them. Readers can comment on the authors' posts, subscribe to them and follow the posts of selected authors in a separate feed. Also, posts can be assigned to a separate thematic group, where all posts on this topic will be collected, if the author specified it when creating the post. The project implements a system of registrations and authorizations. The author or administrator has the right to edit or delete posts.

### Technologies

- Python 3.7
- Django 2.2.6

### Quick start

1. Install and activate the virtual environment
2. Install all packages from [requirements.txt](https://github.com/nick-rebrik/Yatube/blob/master/requirements.txt)<br>
  ```pip install -r requirements.txt```
3. Run in command line:<br>
  ```python manage.py makemigrations```<br>
  ```python manage.py migrate```<br>
  ```python manage.py runserver```
4. Visit the [homepage](http://127.0.0.1:8000/) and start using

> #### _* The project was tested using Django tests._



