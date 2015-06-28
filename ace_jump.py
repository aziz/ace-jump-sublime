import sublime, sublime_plugin

WORD_REGEX = r'\b{}'
CHAR_REGEX = r'{}'

LABELS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"

last_index = 0
hints = []
search_regex = r''

class AceJumpCommand(sublime_plugin.WindowCommand):
    def run(self):
        self.char = ""
        self.target = ""
        self.views = []
        self.breakpoints = []

        for group in range(self.window.num_groups()):
            self.views.append(self.window.active_view_in_group(group))

        self.window.show_input_panel(
            self.get_prompt(),
            "",
            self.submit,
            self.parse,
            self.jump
        )

    def submit(self, command):
        self.jump()

    def parse(self, command):
        global last_index, hints, search_regex

        search_regex = self.get_regex()

        if len(command) == 1:
            self.char = command
            self.breakpoints = []

            last_index = 0
            hints = []

            for view in self.views:
                view.run_command("add_ace_jump_labels", {"char": self.char})
                self.breakpoints.append(last_index)

            return

        if len(command) == 2:
            self.target = command[1]

        self.window.run_command("hide_panel", {"cancel": True})

    def jump(self):
        last_breakpoint = 0

        for breakpoint in self.breakpoints:
            if breakpoint != last_breakpoint:
                view = self.views[self.view_for_index(breakpoint - 1)]
                view.run_command("remove_ace_jump_labels")
                last_breakpoint = breakpoint

        target_index = LABELS.find(self.target)

        if self.target == "" or target_index < 0:
            return

        target_region = hints[target_index].begin()
        target_view = self.views[self.view_for_index(target_index)]

        self.window.focus_view(target_view)
        target_view.run_command("perform_ace_jump", {"target": target_region})

    def view_for_index(self, index):
        for breakpoint in self.breakpoints:
            if index < breakpoint:
                return self.breakpoints.index(breakpoint)

class AceJumpWordCommand(AceJumpCommand):
    def get_prompt(self):
        return "Head char"

    def get_regex(self):
        return WORD_REGEX

class AceJumpCharCommand(AceJumpCommand):
    def get_prompt(self):
        return "Char"

    def get_regex(self):
        return CHAR_REGEX

class AddAceJumpLabelsCommand(sublime_plugin.TextCommand):
    def run(self, edit, char):
        global last_index

        visible_region = self.view.visible_region()
        next_search = visible_region.begin()
        last_search = visible_region.end()

        while (next_search < last_search and last_index < len(LABELS)):
            word = self.view.find(search_regex.format(char), next_search)

            if not word:
                break

            label = LABELS[last_index]
            last_index += 1

            hint = sublime.Region(word.begin(), word.begin() + 1)
            hints.append(hint)

            self.view.replace(edit, hint, label)

            next_search = word.end()

        self.view.add_regions("ace_jump_hints", hints, "invalid")

class RemoveAceJumpLabelsCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        self.view.erase_regions("ace_jump_hints")
        self.view.end_edit(edit)
        self.view.run_command("undo")

class PerformAceJumpCommand(sublime_plugin.TextCommand):
    def run(self, edit, target):
        self.view.sel().clear()
        self.view.sel().add(sublime.Region(target))
        self.view.show(target)