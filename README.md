# Tentron Multi-Site Content Management System

This project implements a flexible multi-site content management system using **Django** and **Wagtail**, with enhanced functionality for managing site settings, permissions, user roles, and media. The system supports dynamic configurations, allowing for customized handling of multiple sites and organizations within a single platform.

### Key Features:

1. **ExtendedSiteMiddleware**: Handles site-specific logic, ensuring that inactive sites redirect to a subscription page and providing a custom 404 page for non-existent extended sites.
   
2. **SiteSettingsAdmin**: Admin interface for managing site-specific settings, ensuring that users only see data for their own sites based on permissions.
   
3. **Dynamic Permissions**: Fine-grained control over model-level permissions for users (e.g., site admins can only access and modify their specific site data).
   
4. **Custom Page and Media Choosers**: Filters media (documents, images, and pages) based on user organization, ensuring that users only access relevant content.
   
5. **User Management**: Enables admins to manage users and roles, with permission restrictions based on the organization.
   
6. **Dynamic CSRF**: Dynamically sets trusted origins for CSRF protection, based on the site’s domain, making it easier to support multi-tenant systems with separate domains.

7. **Docker Integration**: Run commands inside Docker containers as part of Celery tasks, useful for automation and deployment pipelines.

8. **Custom Search Functionality**: Allows for complex search queries within the site’s content, including filters by content type, publish status, and more.


### Contributing

We encourage contributions to this project! Feel free to fork the repository, create a branch, and submit a pull request for any features, bug fixes, or improvements.

If you have any questions, ideas, or issues, please feel free to open an issue on the GitHub repository.

You can find more about me and my work at my personal blog: [www.sufob.com](https://www.sufob.com).

Happy coding!

By Charlie
