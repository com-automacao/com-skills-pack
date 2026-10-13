# CodeIgniter 3 — Deep Dive

Extended CI3 patterns beyond the core SKILL.md. Load this reference when working on CI3-specific features like file uploads, email, caching, HMVC, or custom libraries.

## File Uploads

```php
public function upload()
{
    $config['upload_path']   = './uploads/';
    $config['allowed_types'] = 'gif|jpg|jpeg|png|pdf';
    $config['max_size']      = 2048; // KB
    $config['max_width']     = 1920;
    $config['max_height']    = 1080;
    $config['encrypt_name']  = TRUE;

    $this->load->library('upload', $config);

    if (! $this->upload->do_upload('userfile')) {
        $error = $this->upload->display_errors();
        $this->load->view('upload_form', ['error' => $error]);
    } else {
        $data = $this->upload->data();
        $this->load->view('upload_success', $data);
    }
}
```

Upload data keys: `file_name`, `file_type`, `file_path`, `full_path`, `raw_name`, `orig_name`, `file_ext`, `file_size`, `is_image`, `image_width`, `image_height`.

## Email

```php
$this->load->library('email');

$this->email->from('you@example.com', 'Your Name');
$this->email->to('recipient@example.com');
$this->email->cc('cc@example.com');
$this->email->subject('Order Confirmation');
$this->email->message('<h1>Your Order</h1><p>Details here.</p>');
$this->email->set_mailtype('html');
$this->email->attach('/path/to/invoice.pdf');

if (! $this->email->send()) {
    echo $this->email->print_debugger();
}
```

SMTP config in `application/config/email.php`:

```php
$config['protocol']  = 'smtp';
$config['smtp_host'] = 'ssl://smtp.example.com';
$config['smtp_port'] = 465;
$config['smtp_user'] = 'user@example.com';
$config['smtp_pass'] = 'password';
$config['mailtype']  = 'html';
$config['charset']   = 'utf-8';
```

## Caching

```php
$this->load->driver('cache', ['adapter' => 'file', 'backup' => 'file']);

$data = $this->cache->get('products_list');
if ($data === FALSE) {
    $data = $this->product_model->get_all();
    $this->cache->save('products_list', $data, 3600);
}

$this->cache->delete('products_list');

// Page caching (output cache) — in controller method
$this->output->cache(60); // cache full page for 60 minutes
```

Available drivers: `apc`, `file`, `memcached`, `redis`, `dummy`.

## Pagination

```php
$this->load->library('pagination');

$config['base_url']    = site_url('products/index');
$config['total_rows']  = $this->product_model->count_all();
$config['per_page']    = 20;
$config['uri_segment'] = 3;

$this->pagination->initialize($config);

$offset = $this->uri->segment(3, 0);
$data['products'] = $this->product_model->get_page($config['per_page'], $offset);
$data['pagination'] = $this->pagination->create_links();

$this->load->view('products/index', $data);
```

## Custom Libraries

```php
// application/libraries/My_cart.php
<?php
defined('BASEPATH') or exit('No direct script access allowed');

class My_cart
{
    protected $CI;

    public function __construct($params = [])
    {
        $this->CI =& get_instance();
    }

    public function get_total()
    {
        return $this->CI->db->select_sum('price')->get('cart_items')->row()->price;
    }
}

// Usage
$this->load->library('my_cart');
$total = $this->my_cart->get_total();
```

## HMVC (Modular Extensions)

Many CI3 apps use wiredesignz/hmvc:

```
application/modules/
├── auth/
│   ├── controllers/Auth.php
│   ├── models/Auth_model.php
│   └── views/login.php
├── products/
│   ├── controllers/Products.php
│   ├── models/Product_model.php
│   └── views/index.php
```

Cross-module calls: `Modules::run('auth/check')` or `$this->load->module('auth')`.

## Hooks

```php
// config/hooks.php
$hook['post_controller_constructor'][] = [
    'class'    => 'Auth_hook',
    'function' => 'check_login',
    'filename' => 'Auth_hook.php',
    'filepath' => 'hooks',
];
```

## Logging

```php
// In config.php, set threshold (0 = off, 1 = errors, 2 = +debug, 3 = +info, 4 = all)
$config['log_threshold'] = 1;

log_message('error', 'Something broke: ' . $error_msg);
log_message('debug', 'Variable dump: ' . print_r($data, TRUE));
log_message('info', 'User ' . $user_id . ' logged in');
```

## Common Helpers

```php
// URL
echo base_url('assets/css/style.css');
echo site_url('products/view/5');
redirect('products');

// String
$this->load->helper('string');
$random = random_string('alnum', 16);

// Array
$value = element('key', $array, 'default');

// Date
echo mdate('%Y-%m-%d %H:%i', now());

// Text
echo word_limiter($text, 25);
echo character_limiter($text, 100);
```

## Extended Query Builder

```php
// INSERT BATCH
$this->db->insert_batch('products', [
    ['name' => 'A', 'price' => 10],
    ['name' => 'B', 'price' => 20],
]);

// WHERE IN / LIKE
$this->db->where_in('id', [1, 2, 3])->get('products')->result();
$this->db->like('name', $search)->get('products')->result();

// GROUP BY + HAVING
$this->db->select('category_id, COUNT(*) as total')
    ->group_by('category_id')
    ->having('total >', 5)
    ->get('products')
    ->result();

// COUNT
$count = $this->db->where('active', 1)->count_all_results('products');

// SUBQUERY (no native builder — use raw)
$this->db->where('category_id IN (SELECT id FROM categories WHERE active = 1)', NULL, FALSE);
```

## Common CI3 Pitfalls

1. **Case sensitivity on Linux**: `product_model.php` won't autoload if class is `Product_model`. Always match exactly.
2. **`$this->load` before parent constructor**: Call `parent::__construct()` first.
3. **Raw `$_POST`/`$_GET`**: Always use `$this->input->post()` — returns `NULL` on missing keys.
4. **Forgetting CSRF in AJAX**: Include `csrf_token` in AJAX requests or exempt specific URIs.
5. **Database config in production**: Set `$db['default']['db_debug'] = FALSE`.
6. **`$autoload` bloat**: Only autoload what every request needs. Load per-controller otherwise.
7. **Overwriting `system/`**: Never edit files in `system/` — extend via `application/core/MY_*` classes.
