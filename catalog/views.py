from django.shortcuts import render

# Create your views here.
from .models import Book, Author, BookInstance, Genre, Language

from django.contrib.auth.decorators import login_required


@login_required
def index(request):
    """View function for home page of site."""

    # Generate counts of some of the main objects
    num_books = Book.objects.all().count()
    num_instances = BookInstance.objects.all().count()

    # Available books (status = 'a')
    num_instances_available = BookInstance.objects.filter(status__exact='a').count()

    # The 'all()' is implied by default.
    num_authors = Author.objects.count()

    # Number of visits to this view, as counted in the session variable.
    num_visits = request.session.get('num_visits', 0)
    request.session['num_visits'] = num_visits + 1

    """
    Challenge
    Modify the view to generate counts for genres and books that contain a particular word (case insensitive), and 
    pass the results to the context. You accomplish this in a similar way to creating and using num_books and 
    num_instances_available. Then update the index template to include these variables.
    """
    num_fantasy_genres = Genre.objects.filter(name__icontains='fantasy').count()
    num_thrones_books = Book.objects.filter(title__icontains='thrones').count()

    context = {
        'num_books': num_books,
        'num_instances': num_instances,
        'num_instances_available': num_instances_available,
        'num_authors': num_authors,
        'num_fantasy_genres': num_fantasy_genres,
        'num_thrones_books': num_thrones_books,
        'num_visits': num_visits,
    }

    # Render the HTML template index.html with the data in the context variable
    return render(request, 'index.html', context=context)


# Book List View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import generic


class BookListView(LoginRequiredMixin, generic.ListView):
    model = Book
    paginate_by = 10


class BookDetailView(LoginRequiredMixin, generic.DetailView):
    model = Book


# Author List View
class AuthorListView(LoginRequiredMixin, generic.ListView):
    model = Author
    paginate_by = 10


class AuthorDetailView(LoginRequiredMixin, generic.DetailView):
    model = Author


# Genre List View
class GenreListView(LoginRequiredMixin, generic.ListView):
    model = Genre
    paginate_by = 10


class GenreDetailView(LoginRequiredMixin, generic.DetailView):
    model = Genre


# Language List View
class LanguageListView(LoginRequiredMixin, generic.ListView):
    model = Language
    paginate_by = 10


class LanguageDetailView(LoginRequiredMixin, generic.DetailView):
    model = Language


# A view for getting the list of all books that have been loaned to the current user
class LoanedBooksByUserListView(LoginRequiredMixin, generic.ListView):
    """Generic class-based view listing books on loan to current user."""
    model = BookInstance
    template_name = 'catalog/bookinstance_list_borrowed_user.html'
    paginate_by = 10

    def get_queryset(self):
        return BookInstance.objects.filter(borrower=self.request.user).filter(status__exact='o').order_by('due_back')


# Added as part of challenge!
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.db.models import F  # Required to use query expressions


class BookinstancesAllListView(PermissionRequiredMixin, generic.ListView):
    """Generic class-based view listing all bookinstances. Only visible to users with can_mark_returned permission."""
    model = BookInstance
    permission_required = 'catalog.can_mark_returned'
    template_name = 'catalog/bookinstance_list_all.html'
    paginate_by = 10

    def get_queryset(self):
        return BookInstance.objects.order_by(F('due_back').asc(nulls_last=True))

# Renew books
from django.contrib.auth.decorators import permission_required
from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect
from django.urls import reverse
import datetime
from .forms import RenewBookForm


@permission_required('catalog.can_mark_returned')
def renew_book_librarian(request, pk):
    """View function for renewing a specific BookInstance by librarian"""
    book_inst = get_object_or_404(BookInstance, pk=pk)

    # If this is a POST request then process the Form data
    if request.method == 'POST':

        # Create a form instance and populate it with data from the request (binding):
        form = RenewBookForm(request.POST)

        # Check if the form is valid:
        if form.is_valid():
            # process the data in form.cleaned_data as required (here we just write it to the model due_back field)
            book_inst.due_back = form.cleaned_data['renewal_date']
            book_inst.save()

            # redirect to a new URL:
            return HttpResponseRedirect(reverse('all-bookinstances'))

    # If this is a GET (or any other method) create the default form.
    else:
        proposed_renewal_date = datetime.date.today() + datetime.timedelta(weeks=3)
        form = RenewBookForm(initial={'renewal_date': proposed_renewal_date, })

    return render(request, 'catalog/book_renew_librarian.html', {'form': form, 'bookinst': book_inst})


""" 
Use generic editing views to create pages to add functionality to create, edit, and delete Author records from our 
library — effectively providing a basic reimplementation of parts of the Admin site
"""
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from .models import Author


class AuthorCreate(PermissionRequiredMixin, CreateView):
    model = Author
    permission_required = 'catalog.can_create_author'
    fields = '__all__'
    # initial = {'date_of_death': '05/01/2018', }
    success_url = reverse_lazy('authors')


class AuthorUpdate(PermissionRequiredMixin, UpdateView):
    model = Author
    permission_required = 'catalog.can_update_author'
    fields = ['first_name', 'last_name', 'date_of_birth', 'date_of_death']
    success_url = reverse_lazy('authors')


class AuthorDelete(PermissionRequiredMixin, DeleteView):
    model = Author
    permission_required = 'catalog.can_delete_author'
    success_url = reverse_lazy('authors')


"""
Challenge! Use generic editing views to create pages to add functionality to create, edit, and delete Book records 
from our library
"""
from .models import Book


class BookCreate(PermissionRequiredMixin, CreateView):
    model = Book
    permission_required = 'catalog.can_create_book'
    fields = '__all__'
    success_url = reverse_lazy('books')


class BookUpdate(PermissionRequiredMixin, UpdateView):
    model = Book
    permission_required = 'catalog.can_update_book'
    fields = '__all__'
    success_url = reverse_lazy('books')


class BookDelete(PermissionRequiredMixin, DeleteView):
    model = Book
    permission_required = 'catalog.can_delete_book'
    success_url = reverse_lazy('books')


"""
Use generic editing views to create pages to add functionality to create and delete BookInstance records 
from our library.
"""
from .models import BookInstance


class BookInstanceCreate(PermissionRequiredMixin, CreateView):
    model = BookInstance
    permission_required = 'catalog.can_create_bookinstance'
    fields = '__all__'
    success_url = reverse_lazy('all-bookinstances')


class BookInstanceUpdate(PermissionRequiredMixin, UpdateView):
    model = BookInstance
    permission_required = 'catalog.can_update_bookinstance'
    fields = '__all__'
    success_url = reverse_lazy('all-bookinstances')


class BookInstanceDelete(PermissionRequiredMixin, DeleteView):
    model = BookInstance
    permission_required = 'catalog.can_delete_bookinstance'
    success_url = reverse_lazy('all-bookinstances')


"""
Use generic editing views to create pages to add functionality to create and delete Genre records 
from our library.
"""
from .models import Genre


class GenreCreate(PermissionRequiredMixin, CreateView):
    model = Genre
    permission_required = 'catalog.can_create_genre'
    fields = '__all__'
    success_url = reverse_lazy('genres')


class GenreUpdate(PermissionRequiredMixin, UpdateView):
    model = Genre
    permission_required = 'catalog.can_update_genre'
    fields = '__all__'
    success_url = reverse_lazy('genres')


class GenreDelete(PermissionRequiredMixin, DeleteView):
    model = Genre
    permission_required = 'catalog.can_delete_genre'
    success_url = reverse_lazy('genres')


"""
Use generic editing views to create pages to add functionality to create, edit, and delete Language records 
from our library.
"""
from .models import Language


class LanguageCreate(PermissionRequiredMixin, CreateView):
    model = Language
    permission_required = 'catalog.can_create_language'
    fields = '__all__'
    success_url = reverse_lazy('languages')


class LanguageUpdate(PermissionRequiredMixin, UpdateView):
    model = Language
    permission_required = 'catalog.can_update_language'
    fields = '__all__'
    success_url = reverse_lazy('languages')


class LanguageDelete(PermissionRequiredMixin, DeleteView):
    model = Language
    permission_required = 'catalog.can_delete_language'
    success_url = reverse_lazy('languages')
