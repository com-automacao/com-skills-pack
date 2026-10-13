# CodeIgniter 4 — Deep Dive

Extended CI4 patterns beyond the core SKILL.md. Load this reference when working on CI4-specific features like REST controllers, migrations, testing, Shield auth, services, events, view layouts, or Spark CLI.

## RESTful Resource Controllers

```php
<?php

namespace App\Controllers;

use CodeIgniter\RESTful\ResourceController;

class ProductsApi extends ResourceController
{
    protected $modelName = 'App\Models\ProductModel';
    protected $format    = 'json';

    public function index()    { return $this->respond($this->model->findAll()); }
    public function show($id = null) { return $this->respond($this->model->find($id)); }

    public function create()
    {
        $data = $this->request->getJSON(true);
        if (! $this->model->insert($data)) {
            return $this->failValidationErrors($this->model->errors());
        }
        return $this->respondCreated(['id' => $this->model->getInsertID()]);
    }

    public function update($id = null)
    {
        $data = $this->request->getJSON(true);
        if (! $this->model->update($id, $data)) {
            return $this->failValidationErrors($this->model->errors());
        }
        return $this->respondUpdated(['id' => $id]);
    }

    public function delete($id = null)
    {
        $this->model->delete($id);
        return $this->respondDeleted(['id' => $id]);
    }
}
```

**Response helpers:** `respond($data, 200)`, `respondCreated($data)`, `respondUpdated($data)`, `respondDeleted($data)`, `respondNoContent()`, `fail($messages, 400)`, `failNotFound()`, `failValidationErrors($errors)`, `failForbidden()`, `failUnauthorized()`, `failServerError()`.

## Entities

```php
<?php

namespace App\Entities;

use CodeIgniter\Entity\Entity;

class Product extends Entity
{
    protected $casts = [
        'id'     => 'integer',
        'price'  => 'float',
        'active' => 'boolean',
    ];

    public function setName(string $name): self
    {
        $this->attributes['name'] = trim($name);
        $this->attributes['slug'] = url_title($name, '-', true);
        return $this;
    }
}
```

Set `protected $returnType = Product::class;` in the model.

## Model Callbacks

```php
protected $beforeInsert = ['generateSlug'];
protected $beforeUpdate = ['generateSlug'];

protected function generateSlug(array $data): array
{
    if (isset($data['data']['name'])) {
        $data['data']['slug'] = url_title($data['data']['name'], '-', true);
    }
    return $data;
}
```

Available: `beforeInsert`, `afterInsert`, `beforeUpdate`, `afterUpdate`, `beforeFind`, `afterFind`, `beforeDelete`, `afterDelete`, `beforeInsertBatch`, `afterInsertBatch`, `beforeUpdateBatch`, `afterUpdateBatch`.

## Filters (Middleware)

```php
<?php

namespace App\Filters;

use CodeIgniter\Filters\FilterInterface;
use CodeIgniter\HTTP\RequestInterface;
use CodeIgniter\HTTP\ResponseInterface;

class AuthFilter implements FilterInterface
{
    public function before(RequestInterface $request, $arguments = null)
    {
        if (! session()->get('logged_in')) {
            return redirect()->to('/login');
        }
    }

    public function after(RequestInterface $request, ResponseInterface $response, $arguments = null) {}
}
```

Register in `app/Config/Filters.php`:

```php
public array $aliases = [
    'auth'  => \App\Filters\AuthFilter::class,
    'csrf'  => \CodeIgniter\Filters\CSRF::class,
];

public array $filters = [
    'auth' => ['before' => ['admin/*', 'dashboard']],
    'csrf' => ['before' => ['/*'], 'except' => ['api/*']],
];
```

## Migrations

```bash
php spark make:migration CreateProductsTable
```

```php
<?php

namespace App\Database\Migrations;

use CodeIgniter\Database\Migration;

class CreateProductsTable extends Migration
{
    public function up()
    {
        $this->forge->addField([
            'id'          => ['type' => 'INT', 'constraint' => 11, 'unsigned' => true, 'auto_increment' => true],
            'name'        => ['type' => 'VARCHAR', 'constraint' => 255],
            'slug'        => ['type' => 'VARCHAR', 'constraint' => 255],
            'price'       => ['type' => 'DECIMAL', 'constraint' => '10,2', 'default' => 0],
            'category_id' => ['type' => 'INT', 'constraint' => 11, 'unsigned' => true, 'null' => true],
            'active'      => ['type' => 'TINYINT', 'constraint' => 1, 'default' => 1],
            'created_at'  => ['type' => 'DATETIME', 'null' => true],
            'updated_at'  => ['type' => 'DATETIME', 'null' => true],
            'deleted_at'  => ['type' => 'DATETIME', 'null' => true],
        ]);
        $this->forge->addKey('id', true);
        $this->forge->addKey('slug');
        $this->forge->addForeignKey('category_id', 'categories', 'id', 'SET NULL', 'CASCADE');
        $this->forge->createTable('products');
    }

    public function down()
    {
        $this->forge->dropTable('products');
    }
}
```

## Database Seeding

```bash
php spark make:seeder ProductSeeder
```

```php
<?php

namespace App\Database\Seeds;

use CodeIgniter\Database\Seeder;

class ProductSeeder extends Seeder
{
    public function run()
    {
        $data = [
            ['name' => 'Widget A', 'price' => 9.99, 'active' => 1, 'created_at' => date('Y-m-d H:i:s')],
            ['name' => 'Widget B', 'price' => 19.99, 'active' => 1, 'created_at' => date('Y-m-d H:i:s')],
        ];
        $this->db->table('products')->insertBatch($data);
        $this->call('CategorySeeder');
    }
}
```

## File Uploads

```php
public function upload()
{
    $file = $this->request->getFile('userfile');

    if (! $file->isValid()) {
        return redirect()->back()->with('error', $file->getErrorString());
    }

    if (! $this->validateData([], [
        'userfile' => 'uploaded[userfile]|max_size[userfile,2048]|ext_in[userfile,jpg,jpeg,png,pdf]|mime_in[userfile,image/jpeg,image/png,application/pdf]',
    ])) {
        return redirect()->back()->with('errors', $this->validator->getErrors());
    }

    $path = $file->store('uploads/'); // auto YYYYMMDD subdirs + random name
    return redirect()->back()->with('success', 'File uploaded.');
}

// Multiple files
$files = $this->request->getFileMultiple('images');
foreach ($files as $file) {
    if ($file->isValid() && ! $file->hasMoved()) {
        $file->move(WRITEPATH . 'uploads');
    }
}
```

**UploadedFile methods:** `isValid()`, `hasMoved()`, `getName()`, `getClientName()`, `getClientExtension()`, `guessExtension()`, `getMimeType()`, `getSize()`, `move($path, $name)`, `store($folder)`, `getRandomName()`.

## Email

```php
$email = service('email');

$email->setFrom('you@example.com', 'Your Name');
$email->setTo('recipient@example.com');
$email->setSubject('Order Confirmation');
$email->setMessage('<h1>Your Order</h1><p>Details here.</p>');
$email->setAltMessage('Your Order - Details here.');
$email->attach('/path/to/invoice.pdf');

// Inline image (separate email — setMessage overwrites previous)
$email->clear();
$email->attach('/path/to/logo.png');
$cid = $email->setAttachmentCID('/path/to/logo.png');
$email->setMessage('<img src="cid:' . $cid . '"> <p>Content with inline image</p>');

if (! $email->send()) {
    log_message('error', $email->printDebugger(['headers']));
}
$email->clear();
```

Configure in `.env`:

```ini
email.protocol = smtp
email.SMTPHost = smtp.example.com
email.SMTPUser = user@example.com
email.SMTPPass = password
email.SMTPPort = 587
email.SMTPCrypto = tls
email.mailType = html
```

## Caching

```php
$cache = service('cache');

// Remember pattern (get or compute + cache)
$products = $cache->remember('products_list', 3600, function () {
    return model('ProductModel')->findAll();
});

$cache->delete('products_list');
$cache->deleteMatching('products_*'); // file, redis, predis only
$cache->increment('page_views', 1);
$cache->decrement('stock_count', 1);
$cache->clean(); // wipe all
```

Drivers: `file`, `redis`, `memcached`, `predis`, `wincache`, `dummy`. Configure in `app/Config/Cache.php`.

## Services (Dependency Injection)

```php
// Shared instance (singleton)
$email = service('email');

// New instance
$email = single_service('email');

// Custom service — app/Config/Services.php
public static function paymentGateway(bool $getShared = true)
{
    if ($getShared) {
        return static::getSharedInstance('paymentGateway');
    }
    return new \App\Libraries\StripeGateway(config('Payment')->apiKey);
}

// Usage
$gateway = service('paymentGateway');
```

## Events

```php
// app/Config/Events.php
use CodeIgniter\Events\Events;

Events::on('user_registered', function ($user) {
    service('email')->setTo($user->email)->setSubject('Welcome!')->setMessage(view('emails/welcome', ['user' => $user]))->send();
});

Events::on('order_placed', 'App\Listeners\UpdateInventory::handle', 5); // priority

// Trigger
Events::trigger('user_registered', $user);

// Built-in: pre_system, post_controller_constructor, post_system, email, DBQuery, migrate
```

## View Layouts & Partials

**Layout** (`app/Views/layouts/default.php`):

```php
<!doctype html>
<html>
<head><title><?= $this->renderSection('title') ?></title></head>
<body>
    <?= $this->include('partials/header') ?>
    <main><?= $this->renderSection('content') ?></main>
    <?= $this->include('partials/footer') ?>
</body>
</html>
```

**Child view:**

```php
<?= $this->extend('layouts/default') ?>

<?= $this->section('title') ?>Products<?= $this->endSection() ?>

<?= $this->section('content') ?>
    <h1>Products</h1>
    <?php foreach ($products as $product): ?>
        <div><?= esc($product['name']) ?></div>
    <?php endforeach; ?>
<?= $this->endSection() ?>
```

## View Cells

```bash
php spark make:cell AlertMessageCell
```

```php
// app/Cells/AlertMessageCell.php
namespace App\Cells;
use CodeIgniter\View\Cells\Cell;

class AlertMessageCell extends Cell
{
    public string $type = 'info';
    public string $message = '';
}
```

```php
// app/Cells/alert_message_cell.php
<div class="alert alert-<?= esc($type) ?>"><?= esc($message) ?></div>
```

```php
// Usage
<?= view_cell('AlertMessageCell', ['type' => 'success', 'message' => 'Saved!']) ?>
<?= view_cell('AlertMessageCell', ['type' => 'info', 'message' => 'Hello'], 3600) ?> <!-- cached -->
```

## Custom Spark Commands

```php
<?php

namespace App\Commands;

use CodeIgniter\CLI\BaseCommand;
use CodeIgniter\CLI\CLI;

class AppInfo extends BaseCommand
{
    protected $group       = 'App';
    protected $name        = 'app:info';
    protected $description = 'Displays application information';
    protected $usage       = 'app:info [--env]';
    protected $options     = ['--env' => 'Show environment details'];

    public function run(array $params)
    {
        CLI::write('App: ' . config('App')->appName, 'green');
        if (CLI::getOption('env')) {
            CLI::write('Environment: ' . ENVIRONMENT);
        }
        $this->call('migrate:status');
    }
}
```

## Spark CLI Reference

```bash
# Generators
php spark make:controller Products
php spark make:model ProductModel
php spark make:entity Product
php spark make:filter AuthFilter
php spark make:migration CreateProducts
php spark make:seeder ProductSeeder
php spark make:cell AlertMessageCell
php spark make:command AppInfo
php spark make:validation ProductRules

# Database
php spark migrate
php spark migrate:rollback
php spark migrate:refresh
php spark migrate:status
php spark db:seed ProductSeeder
php spark db:table products

# Utilities
php spark serve
php spark serve --port 9000
php spark routes
php spark filter:check GET /
php spark cache:clear
php spark logs:clear
php spark key:generate
php spark namespaces
php spark phpini:check
```

## Testing

**Setup:**

```bash
composer require --dev phpunit/phpunit
vendor/bin/phpunit
```

**Unit test:**

```php
<?php

namespace Tests\App\Models;

use CodeIgniter\Test\CIUnitTestCase;
use CodeIgniter\Test\DatabaseTestTrait;

class ProductModelTest extends CIUnitTestCase
{
    use DatabaseTestTrait;

    protected $seed = 'Tests\Support\Database\Seeds\ProductSeeder';

    public function testFindReturnsProduct()
    {
        $model = new \App\Models\ProductModel();
        $product = $model->find(1);
        $this->assertIsArray($product);
        $this->assertSame('Widget A', $product['name']);
    }
}
```

**Feature test (HTTP):**

```php
<?php

namespace Tests\App\Controllers;

use CodeIgniter\Test\CIUnitTestCase;
use CodeIgniter\Test\FeatureTestTrait;
use CodeIgniter\Test\DatabaseTestTrait;

class ProductsTest extends CIUnitTestCase
{
    use FeatureTestTrait, DatabaseTestTrait;

    public function testIndexReturns200()
    {
        $result = $this->get('/products');
        $result->assertStatus(200);
        $result->assertSee('Products');
    }

    public function testApiReturnsJson()
    {
        $result = $this->withHeaders(['Accept' => 'application/json'])->get('/api/products');
        $result->assertStatus(200);
        $result->assertJSONFragment(['name' => 'Widget A']);
    }

    public function testCreateWithSession()
    {
        $result = $this->withSession(['logged_in' => true, 'user_id' => 1])
                       ->withBodyFormat('json')
                       ->post('/api/products', ['name' => 'New Product', 'price' => 29.99]);
        $result->assertStatus(201);
    }
}
```

**Controller test:**

```php
use CodeIgniter\Test\ControllerTestTrait;

class ProductsControllerTest extends CIUnitTestCase
{
    use ControllerTestTrait;

    public function testShowReturns404ForMissing()
    {
        $result = $this->controller(\App\Controllers\Products::class)->execute('show', 99999);
        $this->assertFalse($result->isOK());
    }
}
```

## CI Shield Authentication

```bash
composer require codeigniter4/shield
php spark shield:setup
php spark migrate
```

```php
// Route protection
$routes->group('', ['filter' => 'session'], function ($routes) {
    $routes->get('dashboard', 'Dashboard::index');
});
$routes->group('api', ['filter' => 'tokens'], function ($routes) {
    $routes->resource('products');
});

// In controllers
$user = auth()->user();
if (auth()->loggedIn()) { /* authenticated */ }
if ($user->inGroup('admin')) { /* admin */ }
if ($user->can('products.edit')) { /* has permission */ }
```

## Content Negotiation

```php
public function getData()
{
    $data = model('ProductModel')->findAll();
    $format = $this->request->negotiate('media', ['application/json', 'application/xml', 'text/html']);

    return match ($format) {
        'application/json' => $this->response->setJSON($data),
        'application/xml'  => $this->response->setXML($data),
        default            => view('products/index', ['products' => $data]),
    };
}
```

## Logging & Error Handling

```php
// PSR-3 levels: emergency, alert, critical, error, warning, notice, info, debug
log_message('error', 'Payment failed for order {id}', ['id' => $order_id]);
log_message('info', 'User logged in: {email}', ['email' => $user->email]);

// Custom exception views: app/Views/errors/html/error_404.php, error_exception.php
// HTTP exceptions:
throw \CodeIgniter\Exceptions\PageNotFoundException::forPageNotFound('Product not found');
```

## Environment Config

```ini
# .env
CI_ENVIRONMENT = development
app.baseURL = 'http://localhost:8080/'
database.default.hostname = localhost
database.default.database = myapp
database.default.username = root
database.default.password = secret
database.default.DBDriver = MySQLi
encryption.key = hex2bin:your-key-here
```

Never commit `.env`. Set `CI_ENVIRONMENT = production` on production servers.

## Common CI4 Pitfalls

1. **Missing `$allowedFields`**: Insert/update silently drops fields not listed.
2. **Namespace mismatches**: Controller namespace must match directory structure under `app/`.
3. **`.env` not copied**: CI4 ships `.env.example` — copy to `.env` and configure.
4. **`public/` not set as web root**: Server must point to `public/`, not project root.
5. **CSRF on API routes**: Disable CSRF for API endpoints in `Filters.php`.
6. **`writable/` permissions**: Must be writable by the web server.
7. **Returning vs echoing**: CI4 expects `return view(...)` — don't `echo` directly.
8. **Double validation**: Model's `$validationRules` + controller's `$this->validate()` = validating twice. Pick one.
9. **`getPost()` vs `getJSON()`**: Forms use `getPost()`, JSON APIs use `getJSON(true)`.
10. **Shield filter names**: Use `'session'` for web auth, `'tokens'` for API — not `'auth'`.
