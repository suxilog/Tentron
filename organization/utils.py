from wagtail.contrib.modeladmin.helpers import PagePermissionHelper, PermissionHelper


class CommonPermissionHelper(PermissionHelper):
    def user_is_member_of_organization(self, user, obj):
        site = obj.site
        try:

            organization = site.extendedsite.organization
            # check if user in organization.memberships.all()
            return organization.memberships.filter(user=user).exists()

        except Exception as e:
            return False

    def user_can_edit_obj(self, user, obj):
        if user.is_superuser:
            return True
        return self.user_is_member_of_organization(user, obj)

    def user_can_delete_obj(self, user, obj):
        if user.is_superuser:
            return True
        perm_codename = self.get_perm_codename("delete")
        return self.user_has_specific_permission(
            user, perm_codename
        ) and self.user_is_member_of_organization(user, obj)


class CommonPagePermissionHelper(PagePermissionHelper):
    def user_can_list(self, user):
        """
        For models extending Page, permitted actions are determined by
        permissions on individual objects. Rather than check for change
        permissions on every object individually (which would be quite
        resource intensive), we simply always allow the list view to be
        viewed, and limit further functionality when relevant.
        """
        return True

    def user_can_create(self, user):
        """
        For models extending Page, whether or not a page of this type can be
        added somewhere in the tree essentially determines the add permission,
        rather than actual model-wide permissions
        """
        return self.get_valid_parent_pages(user).exists()

    def user_can_edit_obj(self, user, obj):
        perms = obj.permissions_for_user(user)
        return perms.can_edit()

    def user_can_delete_obj(self, user, obj):
        perms = obj.permissions_for_user(user)
        return perms.can_delete()

    def user_can_publish_obj(self, user, obj):
        perms = obj.permissions_for_user(user)
        return obj.live and perms.can_unpublish()

    def user_can_copy_obj(self, user, obj):
        parent_page = obj.get_parent()
        return parent_page.permissions_for_user(user).can_publish_subpage()


class OrganizationPermissionHelper(PermissionHelper):
    def user_is_member_of_organization(self, user, obj):
        site = obj.site
        try:

            organization = site.extendedsite.organization
            # check if user in organization.memberships.all()
            return organization.memberships.filter(user=user).exists()

        except Exception as e:
            return False

    def user_can_edit_obj(self, user, obj):
        if user.is_superuser:
            return True
        return self.user_is_member_of_organization(user, obj)

    def user_can_delete_obj(self, user, obj):
        return self.user_can_edit_obj(user, obj)


class ExtendedSitePermissionHelper(PermissionHelper):
    def user_is_member_of_organization(self, user, obj):
        try:
            organization = obj.organization
            # check if user in organization.memberships.all()
            return organization.memberships.filter(user=user).exists()

        except Exception as e:
            return False

    def user_can_edit_obj(self, user, obj):
        if user.is_superuser:
            return True
        return self.user_is_member_of_organization(user, obj)

    def user_can_delete_obj(self, user, obj):
        if user.is_superuser:
            return True
        # user's group has DELETE extendedsite permission
        if user.groups.filter(permissions__codename="delete_extendedsite").exists():
            return True
        return False
