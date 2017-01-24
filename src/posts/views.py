from django.shortcuts import render , get_object_or_404, redirect
from django.http import HttpResponse,HttpResponseRedirect,Http404
from django.contrib import messages
from django.contrib.contenttypes.models import ContentType

from urllib import quote_plus
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.utils import timezone
from django.db.models import Q

from comments.forms import CommentForm
from comments.models import Comment
from .forms import PostForm
from .models import Post
from .utils import get_read_time
def post_create(request):
	if not request.user.is_staff or not request.user.is_superuser:
		raise Http404	
	form = PostForm(request.POST or None,request.FILES or None)
	if form.is_valid():
		instance = form.save(commit=False)
		instance.user = request.user
		instance.save()
		messages.success(request, "Successfuly Created")
		return HttpResponseRedirect(instance.get_absolute_url())
	#messages.error(request, "Not Successfuly Created")
	
	context ={"form": form,}
	return render(request,"post_form.html",context)

def post_detail(request,slug):
	instance = get_object_or_404(Post,slug=slug)
	if instance.draft or instance.publish > timezone.now().date():
		if not request.user.is_staff or not request.user.is_superuser:#if not admin
			raise Http404
	#you can use this to url-encode the post content
	#or use a custome filter(named urlify)in posts/templatetags 
	share_string = quote_plus(instance.content)

		#you can use this #comments = Comment.objects.filter_by_instance(instance)#
		#or don't and instead you define a comments property in Post class(model) so 
		#comments will be availabe in the Post instance as instance.comments
		#so the 2 ways are basicaly the same
	#comments = Comment.objects.filter_by_instance(instance)
	initial_data = {
		"content_type":instance.get_content_type,
		"object_id" : instance.id
	}
	form = CommentForm(request.POST or None, initial=initial_data)
	if form.is_valid() and request.user.is_authenticated():
		c_type = form.cleaned_data.get("content_type")
		content_type = ContentType.objects.get(model=c_type)
		obj_id = form.cleaned_data.get("object_id")
		content_data = form.cleaned_data.get("content")
		parent_obj = None
		try:
			parent_id = int(request.POST.get("parent_id"))
		except:
			parent_id = None
		if parent_id:
			parent_qs = Comment.objects.filter(id=parent_id)
			if parent_qs.exists() and parent_qs.count()==1:
				parent_obj = parent_qs.first()		
		new_comment, created = Comment.objects.get_or_create(
				#if comment already exist(has same content) it will not be created
				user = request.user,
				content_type = content_type,
				object_id = obj_id,
				content = content_data,
				parent = parent_obj
			)
		return HttpResponseRedirect(new_comment.content_object.get_absolute_url())

	context = {
	"title":instance.title,
	"instance":instance,
	"share_string":share_string,
	#"comments":comments
	"comment_form":form
	}
	return render(request,"post_detail.html",context)

def post_list(request):
	today = timezone.now().date()
	queryset_list = Post.objects.active()#it is modified in models.py,so it doesn't get all posts
	if request.user.is_staff or request.user.is_superuser:#if admin
		queryset_list = Post.objects.all()
	query = request.GET.get('q')
	if query:
		queryset_list= queryset_list.filter(
			Q(title__icontains=query) |
			Q(content__icontains=query) |
			Q(user__first_name__icontains=query) |
			Q(user__last_name__icontains=query)
			).distinct()
	paginator = Paginator(queryset_list, 3) # Show 3 posts per page
	page_request_var = 'page'
	page = request.GET.get(page_request_var)
	try:
		queryset = paginator.page(page)
	except PageNotAnInteger:
		# If page is not an integer, deliver first page.
		queryset = paginator.page(1)
	except EmptyPage:
		# If page is out of range (e.g. 9999), deliver last page of results.
		queryset = paginator.page(paginator.num_pages)

	context = {
		"title":"list",
		"object_list" :queryset,
		"page_request_var":page_request_var,
		"today":today
	}
	return render(request,"post_list.html",context)


def post_update(request,slug):
	if not request.user.is_staff or not request.user.is_superuser:
		raise Http404
	instance = get_object_or_404(Post,slug=slug)
	form = PostForm(request.POST or None,request.FILES or None,instance=instance)
	if form.is_valid():#works while post method is applied on the form#not valid while get method
		instance = form.save(commit=False)
		instance.save()
		messages.success(request, "Successfuly Updated")
		return HttpResponseRedirect(instance.get_absolute_url())
	
	#messages.error(request, "Not Successfuly Updated")
	context = {
	"title":instance.title,
	"instance":instance,
	"form":form
	}
	return render(request,"post_form.html",context)
def post_delete(request,slug):
	if not request.user.is_staff or not request.user.is_superuser:
		raise Http404
	instance = get_object_or_404(Post,slug=slug)
	instance.delete()
	messages.success(request, "Post Deleted")
	return redirect('posts:list')