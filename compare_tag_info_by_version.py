import pprint
import sys

import asdf


class ChangeSet:
    def __init__(self):
        # added_tags, removed_tags, support_added, support_removed
        self.by_tag = {}
        self.extension_changes = {}
        # added_types, removed_types
        self.by_type = {}

    def tag_change(self, new_info, version, change_name):
        if change_name not in self.by_tag:
            self.by_tag[change_name] = {}
        current_info = self.by_tag[change_name]
        for tag in new_info:
            if tag in current_info:
                current_info[tag]['versions'].add(version)
            else:
                info = new_info[tag].copy()
                info['versions'] = set([version])
                current_info[tag] = info

    def extension_change(self, tag, tag_info, version, old_extension, new_extension):
        key = (tag, old_extension, new_extension)
        if key not in self.extension_changes:
            self.extension_changes[key] = tag_info.copy()
            self.extension_change[key]['versions'] = set([version])
        else:
            self.extension_change[key]['versions'].add(version)

    def type_change(self, tag, tag_info, version, changes, change_name):
        if change_name not in self.by_type:
            self.by_type[change_name] = {}
        current_info = self.by_type[change_name] = {}
        key = (tag, changes)
        if key not in current_info:
            current_info[key] = tag_info.copy()
            current_info[key]['versions'] = set([version])
        else:
            current_info[key]['versions'].add(version)

    def __len__(self):
        return len(self.by_tag) + len(self.extension_changes) + len(self.by_type)

    def render(self):
        if not len(self):
            print("No changes :white_check_mark:")
            return

        if "added_tags" in self.by_tag:
            print(f"Tag Additions")
            print("-----")
            for tag in self.by_tag["added_tags"]:
                info = self.by_tag["added_tags"][tag]
                versions = ", ".join(sorted(list(info["versions"])))
                short_msg = f"tag <code>{tag}</code> added in versions {versions}"
                long_msg = f"<code>{pprint.pformat(info)}</code>"
                print(f"<details><summary>{short_msg}</summary>{long_msg}</details>")

        if "support_added" in self.by_tag:
            print(f"Tag Support Additions")
            print("-----")
            for tag in self.by_tag["support_added"]:
                info = self.by_tag["support_added"][tag]
                versions = ", ".join(sorted(list(info["versions"])))
                short_msg = f"tag <code>{tag}</code> added support in versions {versions}"
                long_msg = f"<code>{pprint.pformat(info)}</code>"
                print(f"<details><summary>{short_msg}</summary>{long_msg}</details>")

        if "support_removed" in self.by_tag:
            print(f":warning: Tag Support Removals :warning:")
            print("-----")
            for tag in self.by_tag["support_removed"]:
                info = self.by_tag["support_removed"][tag]
                versions = ", ".join(sorted(list(info["versions"])))
                short_msg = f"tag <code>{tag}</code> removed support in versions {versions}"
                long_msg = f"<code>{pprint.pformat(info)}</code>"
                print(f"<details><summary>{short_msg}</summary>{long_msg}</details>")

        if len(self.extension_changes):
            print("Tag extension changes")
            print("-----")
            for key in self.extension_changes:
                tag, old_extension, new_extension = key
                info = self.extension_changes[key]
                versions = ", ".join(sorted(list(info["versions"])))
                short_msg = f"tag <code>{tag}</code> changed from extension <code>{old_extension}</code> to <code>{new_extension}</code> in versions {versions}"
                long_msg = f"<code>{pprint.pformat(info)}</code>"
                print(f"<details><summary>{short_msg}</summary>{long_msg}</details>")

        if "added_types" in self.by_type:
            print(f"Type additions")
            print("-----")
            for key in self.by_type["added_types"]:
                tag, type_changes = key
                info = self.by_type["added_types"][key]
                versions = ", ".join(sorted(list(info["versions"])))
                type_strings = ", ".join(sorted(list(type_changes)))
                short_msg = f"tag <code>{tag}</code> added support for types {type_strings} in versions {versions}"
                long_msg = f"<code>{pprint.pformat(info)}</code>"
                print(f"<details><summary>{short_msg}</summary>{long_msg}</details>")

        if "removed_types" in self.by_type:
            print(f":warning: Type additions :warning:")
            print("-----")
            for key in self.by_type["removed_types"]:
                tag, type_changes = key
                info = self.by_type["removed_types"][key]
                versions = ", ".join(sorted(list(info["versions"])))
                type_strings = ", ".join(sorted(list(type_changes)))
                short_msg = f"tag <code>{tag}</code> removed support for types {type_strings} in versions {versions}"
                long_msg = f"<code>{pprint.pformat(info)}</code>"
                print(f"<details><summary>{short_msg}</summary>{long_msg}</details>")


pre_fn, post_fn = sys.argv[1], sys.argv[2]

changeset = ChangeSet()

with (
    asdf.open(pre_fn) as pre_af,
    asdf.open(post_fn) as post_af,
):
    pre_info = pre_af['tag_info_by_version']
    post_info = post_af['tag_info_by_version']

    pre_versions = pre_info.keys()
    post_versions = post_info.keys()

    if pre_versions != post_versions:
        # TODO different asdf standard versions
        raise NotImplementedError

    for version in pre_versions:
        pre_tags = set(pre_info[version])
        post_tags = set(post_info[version])

        # TODO check for tag version changes where an old tag version
        # will be removed and a new version added (this should only be allowed
        # to happen in the dev version of the standard).
        added_tags = post_tags - pre_tags
        if added_tags:
            new_info = {t: post_info[version][t] for t in added_tags}
            changeset.tag_change(new_info, version, 'added_tags')
            for tag in added_tags:
                added_tag = post_info[version][tag]

        removed_tags = pre_tags - post_tags
        if removed_tags:
            new_info = {t: pre_info[version][t] for t in removed_tags}
            changeset.tag_change(new_info, version, 'removed_tags')
            for tag in removed_tags:
                removed_tag = pre_info[version][tag]

        for tag in pre_tags & post_tags:
            pre_tag = pre_info[version][tag]
            post_tag = post_info[version][tag]

            if not pre_tag['supported'] and post_tag['supported']:
                changeset.tag_change({tag: post_tag}, version, "support_added")
                # TODO continue with other checks?
                continue
            elif pre_tag['supported'] and not post_tag['supported']:
                changeset.tag_change({tag: post_tag}, version, "support_removed")
                # TODO continue with other checks?
                continue
            elif not pre_tag['supported']:
                # tag is not supported in either pre or post
                # TODO continue with other checks?
                continue

            # TODO check extension_uris (for not just handling extension)

            # supported in both pre and post
            pre_extension = pre_tag["handling_extension_uri"]
            post_extension = pre_tag["handling_extension_uri"]
            if pre_extension != post_extension:
                changeset.extension_change(tag, post_tag, version, pre_extension, post_extension)

            # TODO check linked schemas

            pre_types = set(pre_tag["types"])
            post_types = set(post_tag["types"])

            added_types = post_types - pre_types
            if added_types:
                changeset.type_change(tag, post_tag, version, added_types, "added_types")

            removed_types = pre_types - post_types
            if removed_types:
                changeset.type_change(tag, post_tag, version, removed_types, "removed_types")

changeset.render()
