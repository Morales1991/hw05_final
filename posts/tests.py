from django.test import TestCase, Client
from django.core.cache import cache
from django.core.cache.utils import make_template_fragment_key

from .models import User, Post, Group, Follow


class HomeWorkTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.test_user = User.objects.create_user(username='Vasya', email='Vasya@pivko.ru', password='12345678')
        self.test_user_2 = User.objects.create_user(username='Petya', email='Petya@zoj.ru', password='12345678')
        self.test_Dude = User.objects.create_user(username='Dude', email='Dude@BigLebowski.ru', password='12345678')
        self.test_group = Group.objects.create(title='Котики', slug='cats', description='пушистые сволочи')
        self.client.login(username='Vasya', password='12345678')
        cache.clear()

    def test_profile(self): 
        response = self.client.get(f'/{self.test_user.username}/')
        self.assertEqual(response.status_code, 200)

    def test_user_createPost(self):
        response = self.client.get('/new')
        self.assertEqual(response.status_code, 200)
        
        self.client.post('/new', {'text': 'test'})
        self.assertTrue(Post.objects.filter(text='test', author=self.test_user).exists())

    def test_anonim_user(self):
        self.client.logout()
        response = self.client.get('/new')
        self.assertRedirects(response, '/auth/login/?next=/new', status_code=302, target_status_code=200, msg_prefix='', fetch_redirect_response=True)

    def test_pages_with_post(self):
        self.client.login(username='Vasya', password='12345678')
        post = Post.objects.create(author=self.test_user, text='еще какой то текст')
        response = self.client.get('')
        self.assertContains(response, post)
        response = self.client.get(f'/{self.test_user.username}/{post.id}/')
        self.assertContains(response, post)

    def test_edit_post(self):
        new_text = 'все еще хочу на море' 
        post = Post.objects.create(author=self.test_user, text='хочу на море')

        response = self.client.post(f'/{self.test_user.username}/{post.id}/edit/', {'text': new_text})
        self.assertRedirects(response, f'/{self.test_user.username}/{post.id}/', status_code=302, 
                                        target_status_code=200, msg_prefix='', fetch_redirect_response=True)
        
        response = self.client.get('')
        self.assertContains(response, new_text)
        
        response = self.client.get(f'/{self.test_user.username}/')
        self.assertContains(response, new_text)
       
        response = self.client.get(f'/{self.test_user.username}/{post.id}/')
        self.assertContains(response, new_text)

    def test_404(self):
        response = self.client.get('default_page')
        self.assertEqual(response.status_code, 404)

    def test_img(self):
        post = Post.objects.create(author=self.test_user, group=self.test_group,  
                                    text='еще какой то текст', image='/home/vlad/Рабочий стол/Учеба/hw05_final/media/posts/1.jpeg') #не получилось подгрузить фаил через заполнение формы, это возможно?
        
        response = self.client.get('')
        self.assertContains(response, '<img')

        response = self.client.get(f'/{self.test_user.username}/')
        self.assertContains(response, '<img')

        response = self.client.get(f'/{self.test_user.username}/{post.id}/')
        self.assertContains(response, '<img')

        response = self.client.get(f'/group/{self.test_group.slug}/')
        self.assertContains(response, '<img')

    def test_fake_img(self):
        with open('media/posts/2.txt', 'rb') as img:
            response = self.client.post('/new', {'text': 'ложная картинка', 'image': img})
            self.assertFormError(response, 'form', 'image', 'Загрузите правильное изображение. Файл, который вы загрузили, поврежден или не является изображением.')

    def test_cache(self):
        response = self.client.get('')
        key = make_template_fragment_key('index_page', ['<Page 1 of 1>'])
        html_cache = cache.get(key)
        self.assertIn(html_cache,str(response.content.decode()))

    def test_follow(self):
        response = self.client.get(f'/{self.test_user_2.username}/follow')
        count = Follow.objects.filter(author=self.test_user_2, user=self.test_user).count()
        self.assertEqual(count, 1)

        response = self.client.get(f'/{self.test_user_2.username}/unfollow')
        count = Follow.objects.filter(author=self.test_user_2, user=self.test_user).count()
        self.assertEqual(count, 0)

    def test_follow_post(self):
        response = self.client.get(f'/{self.test_user_2.username}/follow')
        post = Post.objects.create(author=self.test_user_2, text='пост для ленты')
        post_Dude = Post.objects.create(author=self.test_Dude, text='пост Чувака')

        response = self.client.get('/follow/')
        self.assertContains(response, post)
        self.assertNotContains(response, post_Dude)

    def test_comment(self):
        Post.objects.create(author=self.test_user, text='пост для коммента')
        self.client.logout()
        response = self.client.get(f'/{self.test_user.username}/1/comment/')
        self.assertRedirects(response, '/auth/login/?next=/'f'{self.test_user.username}/1/comment/', status_code=302, target_status_code=200, msg_prefix='', fetch_redirect_response=True)

