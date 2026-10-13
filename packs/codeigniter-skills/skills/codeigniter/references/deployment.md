# Deployment & Migration

Server configuration, production hardening, and the complete CI3 → CI4 migration reference.

## Server Configuration

### Apache (.htaccess)

**CI3** — place in project root:

```apache
RewriteEngine On
RewriteCond %{REQUEST_FILENAME} !-f
RewriteCond %{REQUEST_FILENAME} !-d
RewriteRule ^(.*)$ index.php/$1 [L]
```

**CI4** — the `public/` directory includes this by default. Ensure `AllowOverride All` is set in Apache config.

### Nginx

**CI3:**

```nginx
server {
    listen 80;
    server_name example.com;
    root /var/www/project;
    index index.php;

    location / {
        try_files $uri $uri/ /index.php$is_args$args;
    }

    location ~ \.php$ {
        fastcgi_pass unix:/run/php/php-fpm.sock;
        fastcgi_param SCRIPT_FILENAME $document_root$fastcgi_script_name;
        include fastcgi_params;
    }

    location ~ /\. { deny all; }
}
```

**CI4** — same but set `root /var/www/project/public;`

## Production Deployment Checklist

- [ ] Set `CI_ENVIRONMENT = production` in `.env` (CI4) or `ENVIRONMENT` constant in `index.php` (CI3)
- [ ] Point web root to `public/` (CI4) — never expose project root
- [ ] `writable/` directory: `chmod -R 775`, owned by web server user
- [ ] Remove `public/index.php` debug toolbar references if present
- [ ] Disable `display_errors` in `php.ini`
- [ ] Set `database.default.DBDebug = false` in production `.env`
- [ ] Enable OPcache (`opcache.enable=1`)
- [ ] Configure production cache driver (Redis/Memcached instead of file)
- [ ] Set `session.cookie_secure = true` and `session.cookie_httponly = true`
- [ ] Run `php spark cache:clear` after deploy
- [ ] Use `composer install --no-dev --optimize-autoloader` for production

## CI3 → CI4 Full Migration Reference

| CI3 | CI4 |
|-----|-----|
| `$this->load->model('x')` | `model('XModel')` or DI |
| `$this->load->view('x', $data)` | `return view('x', $data)` |
| `$this->load->library('x')` | `service('x')` or `new X()` |
| `$this->load->helper('x')` | `helper('x')` |
| `$this->input->post('x')` | `$this->request->getPost('x')` |
| `$this->input->get('x')` | `$this->request->getGet('x')` |
| `$this->input->post('x', TRUE)` | `$this->request->getPost('x')` (no XSS param — use `esc()` in views) |
| `$this->db->get('table')` | `$db->table('table')->get()` |
| `$query->result()` | `$query->getResult()` |
| `$query->row()` | `$query->getRow()` |
| `$query->result_array()` | `$query->getResultArray()` |
| `$query->num_rows()` | `$query->getNumRows()` |
| `$this->db->insert_id()` | `$db->insertID()` |
| `$this->db->affected_rows()` | `$db->affectedRows()` |
| `$this->db->count_all_results()` | `$builder->countAllResults()` |
| `$this->db->trans_start()` | `$db->transStart()` |
| `$this->db->trans_complete()` | `$db->transComplete()` |
| `redirect('url')` | `return redirect()->to('url')` |
| `show_404()` | `throw PageNotFoundException::forPageNotFound()` |
| `show_error($msg)` | `throw new \RuntimeException($msg)` |
| `$this->session->userdata('x')` | `session()->get('x')` |
| `$this->session->set_userdata('k', $v)` | `session()->set('k', $v)` |
| `$this->session->set_flashdata('k', $v)` | `session()->setFlashdata('k', $v)` |
| `$this->session->flashdata('k')` | `session()->getFlashdata('k')` |
| `html_escape($x)` | `esc($x)` |
| `$this->upload->do_upload('f')` | `$this->request->getFile('f')->move(...)` |
| `$this->email->send()` | `service('email')->send()` |
| `$this->cache->get('k')` | `service('cache')->get('k')` |
| `$this->pagination->create_links()` | `$model->pager->links()` |
| `log_message('error', $msg)` | `log_message('error', $msg)` (same API) |
| `$route['x'] = 'y'` | `$routes->get('x', 'Y::method')` |
| `$route['default_controller']` | `$routes->get('/', 'Home::index')` |
| Hooks (`$hook[]`) | Filters (middleware) |
| `CI_Controller` | `BaseController` |
| `CI_Model` | `CodeIgniter\Model` |
| No namespaces | PSR-4 namespaces |
| No CLI generator | `php spark make:*` |
| No built-in testing | PHPUnit + `CIUnitTestCase` |
| Ion Auth / Community libs | CI Shield (official) |
| `$config` arrays in `config/*.php` | Classes in `app/Config/*.php` + `.env` |
| `application/` | `app/` |
| `index.php` in root | `index.php` in `public/` |
