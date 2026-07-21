# -*- coding: utf-8 -*-
"""Flask CLI management commands."""
import secrets
import click
from flask import current_app


def register_commands(app):
    @app.cli.command('create-admin')
    @click.option('--email', '-e', default='season@maybi.cn', help='Admin email')
    @click.option('--name', '-n', default='Admin', help='Admin display name')
    def create_admin(email, name):
        """Create a super admin user with full backend permissions."""
        import application.models as Models
        from configs.enum import USER_ROLE

        existing = Models.User.objects(account__email=email).first()
        if existing:
            if USER_ROLE.ADMIN not in existing.roles:
                existing.update(push__roles=USER_ROLE.ADMIN)
                click.echo(f'User {email} already exists. Added ADMIN role.')
            else:
                click.echo(f'User {email} already has ADMIN role.')
            return

        password = secrets.token_urlsafe(12)
        user = Models.User(name=name)
        user.account = Models.UserAccount(
            email=email,
            password=password,
            is_email_verified=True,
        )
        user.roles = [USER_ROLE.ADMIN]
        user.save()

        click.echo('=' * 60)
        click.echo('Super admin created successfully!')
        click.echo(f'  Email:    {email}')
        click.echo(f'  Password: {password}')
        click.echo(f'  Name:     {name}')
        click.echo(f'  Roles:    {user.roles}')
        click.echo('=' * 60)
        click.echo('Log in at /admin/login to access the backend.')
