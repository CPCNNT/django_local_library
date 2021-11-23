from django.db import models

# Create your models here.
"""
Genre model

This model is used to store information about the book category — for example whether it is fiction or non-fiction, 
romance or military history, etc.

The model has a single CharField field (name), which is used to describe the genre (this is limited to 200 characters 
and has some help_text. At the end of the model we declare a __str__() method, which simply returns the name of the 
genre defined by a particular record. No verbose name has been defined, so the field will be called Name in forms.
"""


class Genre(models.Model):
    """Model representing a book genre (e.g. Science Fiction, Non Fiction)."""
    name = models.CharField(max_length=200, help_text="Enter a book genre (e.g. Science Fiction, French Poetry etc.)")

    class Meta:
        ordering = ['name']
        permissions = (
            ('can_create_genre', 'Create genre'),
            ('can_update_genre', 'Update genre'),
            ('can_delete_genre', 'Delete genre'),
        )

    def get_absolute_url(self):
        """Returns the url to access a particular genre instance."""
        return reverse('genre-detail', args=[str(self.id)])

    def __str__(self):
        """String for representing the Model object (in Admin site etc.)"""
        return self.name


"""
Language model

Imagine a local benefactor donates a number of new books written in another language (say, Farsi). The challenge is to 
work out how these would be best represented in our library website, and then to add them to the models.

Some things to consider:
1. Should "language" be associated with a Book, BookInstance, or some other object?
2. Should the different languages be represented using model, a free text field, or a hard-coded selection list?
"""


class Language(models.Model):
    """Model representing a Language (e.g. English, French, Japanese, etc.)"""
    name = models.CharField(max_length=200,
                            help_text="Enter the book's natural language (e.g. English, French, Japanese etc.)")

    class Meta:
        ordering = ['name']
        permissions = (
            ('can_create_language', 'Create language'),
            ('can_update_language', 'Update language'),
            ('can_delete_language', 'Delete language'),
        )

    def get_absolute_url(self):
        """Returns the url to access a particular language instance."""
        return reverse('language-detail', args=[str(self.id)])

    def __str__(self):
        """String for representing the Model object (in Admin site etc.)"""
        return self.name


"""
Book model

The book model represents all information about an available book in a general sense, but not a particular physical 
"instance" or "copy" available for loan. The model uses a CharField to represent the book's title and isbn (note how 
the isbn specifies its label as "ISBN" using the first unnamed parameter because the default label would otherwise be 
"Isbn"). The model uses TextField for the summary, because this text may need to be quite long.

The genre is a ManyToManyField, so that a book can have multiple genres and a genre can have many books. The author is 
declared as ForeignKey, so each book will only have one author, but an author may have many books (in practice a book 
might have multiple authors, but not in this implementation!)

In both field types the related model class is declared as the first unnamed parameter using either the model class or 
a string containing the name of the related model. You must use the name of the model as a string if the associated 
class has not yet been defined in this file before it is referenced! The other parameters of interest in the author 
field are null=True, which allows the database to store a Null value if no author is selected, and 
on_delete=models.SET_NULL, which will set the value of the author to Null if the associated author record is deleted.

The model also defines __str__() , using the book's title field to represent a Book record. The final method, 
get_absolute_url() returns a URL that can be used to access a detail record for this model (for this to work we will 
have to define a URL mapping that has the name book-detail, and define an associated view and template).
"""
from django.urls import reverse  # Used to generate URLs by reversing the URL patterns


class Book(models.Model):
    """Model representing a book (but not a specific copy of a book)."""
    title = models.CharField(max_length=200)
    author = models.ForeignKey('Author', on_delete=models.SET_NULL, null=True)
    # Foreign Key used because book can only have one author, but authors can have multiple books
    # Author as a string rather than object because it hasn't been declared yet in the file.
    summary = models.TextField(max_length=3000, blank=True, help_text="Enter a brief description of the book")
    isbn = models.CharField('ISBN', max_length=13, blank=True,
                            help_text='10 or 13 Characters <a href="https://www.isbn-international.org/content/what'
                                      '-isbn" target="_blank">ISBN number</a>')
    genre = models.ManyToManyField(Genre, help_text="Select a genre for this book")
    # ManyToManyField used because genre can contain many books. Books can cover many genres.
    # Genre class has already been defined so we can specify the object above.
    language = models.ForeignKey('Language', on_delete=models.SET_NULL, null=True)

    class Meta:
        ordering = ['title', 'author']
        permissions = (
            ("can_create_book", "Create book"),
            ("can_update_book", "Update book"),
            ("can_delete_book", "Delete book"),
        )

    def display_genre(self):
        """Creates a string for the Genre. This is required to display genre in Admin."""
        return ', '.join([genre.name for genre in self.genre.all()[:3]])

    display_genre.short_description = 'Genre'

    def get_absolute_url(self):
        """Returns the url to access a particular book instance."""
        return reverse('book-detail', args=[str(self.id)])

    def __str__(self):
        """String for representing the Model object."""
        return self.title


"""
BookInstance model

The BookInstance represents a specific copy of a book that someone might borrow, and includes information about 
whether the copy is available or on what date it is expected back, "imprint" or version details, and a unique id for 
the book in the library.

The model uses
1. ForeignKey to identify the associated Book (each book can have many copies, but a copy can only have one Book).
2. CharField to represent the imprint (specific release) of the book.

We additionally declare a few new types of field:
1. UUIDField is used for the id field to set it as the primary_key for this model. This type of field allocates a 
globally unique value for each instance (one for every book you can find in the library).
2. DateField is used for the due_back date (at which the book is expected to come available after being borrowed or in 
maintenance). This value can be blank or null (needed for when the book is available). The model metadata (Class Meta) 
uses this field to order records when they are returned in a query.
3. status is a CharField that defines a choice/selection list. As you can see, we define a tuple containing tuples of 
key-value pairs and pass it to the choices argument. The value in a key/value pair is a display value that a user can 
select, while the keys are the values that are actually saved if the option is selected. We've also set a default 
value of 'm' (maintenance) as books will initially be created unavailable before they are stocked on the shelves.

The model __str__() represents the BookInstance object using a combination of its unique id and the associated 
Book's title.
"""
import uuid  # Required for unique book instances
from datetime import date
from django.contrib.auth.models import User  # Required to assign User as a borrower
from django.db.models import F  # Required to use query expressions


class BookInstance(models.Model):
    """Model representing a specific copy of a book (i.e. that can be borrowed from the library)."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4,
                          help_text="Unique ID for this particular book across whole library")
    book = models.ForeignKey('Book', on_delete=models.SET_NULL, null=True)
    imprint = models.CharField(max_length=200)
    due_back = models.DateField(null=True, blank=True, help_text='Enter the date in the form of yyyy-mm-dd')
    borrower = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    @property
    def is_overdue(self):
        if self.due_back and date.today() > self.due_back:
            return True
        return False

    LOAN_STATUS = (
        ('m', 'Maintenance'),
        ('o', 'On loan'),
        ('a', 'Available'),
        ('r', 'Reserved'),
    )

    status = models.CharField(max_length=1, choices=LOAN_STATUS, blank=True, default='m', help_text='Book availability')

    class Meta:
        ordering = [F('due_back').asc(nulls_last=True)]
        permissions = (
            ("can_mark_returned", "Set book as returned"),
            ("can_create_bookinstance", "Create bookinstance"),
            ("can_update_bookinstance", "Update bookinstance"),
            ("can_delete_bookinstance", "Delete bookinstance"),
        )

    def __str__(self):
        """String for representing the Model object"""
        return '{0} ({1})'.format(self.id, self.book.title)


"""
Author model

The model defines an author as having a first name, last name, date of birth, and (optional) date of death. It 
specifies that by default the __str__() returns the name in last name, firstname order. The get_absolute_url() method 
reverses the author-detail URL mapping to get the URL for displaying an individual author.
"""


class Author(models.Model):
    """Model representing an author."""
    first_name = models.CharField(max_length=100)  # first name = given name = 名
    last_name = models.CharField(max_length=100)  # last name = family name = surname = 姓
    date_of_birth = models.DateField(null=True, blank=True, help_text='Enter the date in the form of yyyy-mm-dd')
    date_of_death = models.DateField('Died', null=True, blank=True,
                                     help_text='Enter the date in the form of yyyy-mm-dd')

    class Meta:
        ordering = ['last_name', 'first_name']
        permissions = (
            ("can_create_author", "Create author"),
            ("can_update_author", "Update author"),
            ("can_delete_author", "Delete author"),
        )

    def get_absolute_url(self):
        """Returns the url to access a particular author instance."""
        return reverse('author-detail', args=[str(self.id)])

    def __str__(self):
        """String for representing the Model object."""
        return '{0} {1}'.format(self.first_name, self.last_name)


"""
Caution!
You should re-run the database migrations everytime you make changes in this file.
"""
