# CS50W Project 1

## Web Programming with Python and JavaScript

I build a book review website called 'BooksProject' with the following functionalities/features;

- Registration and login: Users will register by providing their fullname, email, username and password. I made used of flash's 'check_password_hash', 'generate_password_hash' functions to hash and store the users password. User can't register with same username twice. Users will login using their username and password.

- Search: I implemented a search program where users can search for books using title, author, isbn. 

- API: Made API request to Goodreads API to get books reviews and another to Open Library to get book covers using Book's ISBN. I also created my own API for users to access and query for books using ISBN.
