from __future__ import unicode_literals, print_function
import os
import fnmatch
import bible_books
from general_tools.file_utils import write_file, read_file
from general_tools.file_utils import copy_tree
from shutil import copy

class Preprocessor(object):
    def __init__(self, manifest, source_dir, output_dir, quiet=False):
        self.manifest = manifest
        self.source_dir = source_dir  # Local directory
        self.output_dir = output_dir  # Local directory
        self.quiet = quiet

    def run(self):
        if os.path.isdir(os.path.join(self.source_dir, 'content')):
            content_dir = os.path.join(self.source_dir, 'content')
        else:
            content_dir = self.source_dir

        copy_tree(content_dir, self.output_dir)


class UsfmPreprocessor(Preprocessor):
    def __init__(self, *args, **kwargs):
        super(UsfmPreprocessor, self).__init__(*args, **kwargs)


class BibleUsfmPreprocessor(UsfmPreprocessor):
    def __init__(self, *args, **kwargs):
        super(BibleUsfmPreprocessor, self).__init__(*args, **kwargs)


class MarkdownPreprocessor(Preprocessor):
    def __init__(self, *args, **kwargs):
        super(MarkdownPreprocessor, self).__init__(*args, **kwargs)


class ObsMarkdownPreprocessor(MarkdownPreprocessor):
    def __init__(self, *args, **kwargs):
        super(ObsMarkdownPreprocessor, self).__init__(*args, **kwargs)

    def run(self):
        content_dir = self.source_dir
        if os.path.isdir(os.path.join(self.source_dir, 'content')):
            content_dir = os.path.join(self.source_dir, 'content')
            # if it is a RC v0.2 container with ##/01.md, we copy each 01.md file (or intro.md file) into output_dir
            if os.path.isfile(os.path.join(self.source_dir, 'manifest.yaml')):
                dirs = [name for name in os.listdir(content_dir) if os.path.isdir(os.path.join(content_dir, name))]
                for d in dirs:
                    f = None
                    if os.path.isfile(os.path.join(content_dir, d, "01.md")):
                        f = os.path.join(content_dir, d, '01.md')
                    elif os.path.isfile(os.path.join(content_dir, d, 'intro.md')):
                        f = os.path.join(content_dir, d, 'intro.md')
                    if f:
                        copy(f, os.path.join(self.output_dir, '{0}.md'.format(d)))
                return
        # otherwise we just copy the content_dir to output_dir
        copy_tree(content_dir, self.output_dir)


class TsObsMarkdownPreprocessor(ObsMarkdownPreprocessor):
    ignoreDirectories = ['.git', '00']
    framesIgnoreFiles = ['.DS_Store', 'reference.txt', 'title.txt']

    def __init__(self, *args, **kwargs):
        super(TsObsMarkdownPreprocessor, self).__init__(*args, **kwargs)


    def get_chapter_title(self, chapter):
        """
        Get a chapter title.

        if the title file does not exist, it will hand back the number with a period only.
        """
        title_file = os.path.join(self.source_dir, chapter, 'title.txt')
        title = chapter.lstrip('0') + '. '
        if os.path.exists(title_file):
            contents = read_file(title_file)
            title = contents.strip()
        return title


    def get_chapter_reference(self, chapter):
        """Get the chapters reference text"""
        reference_file = os.path.join(self.source_dir, chapter, 'reference.txt')
        reference = ''
        if os.path.exists(reference_file):
            contents = read_file(reference_file)
            reference = contents.strip()
        return reference

    def get_chapter_frames(self, chapter):
        frames = []
        chapter_dir = os.path.join(self.source_dir, chapter)
        for frame in os.listdir(chapter_dir):
            if not frame in self.framesIgnoreFiles:
                text = read_file(os.path.join(chapter_dir, frame))
                frames.append({
                    'id': chapter + '-' + frame.strip('.txt'),
                    'text': text
                })
        return frames

    def get_chapters(self):
        chapters = []
        for id in os.listdir(self.source_dir):
            if os.path.isdir(os.path.join(self.source_dir, id)) and id not in self.ignoreDirectories:
                chapters.append({
                    'id': id,
                    'title': self.get_chapter_title(id),
                    'reference': self.get_chapter_reference(id),
                    'frames': self.get_chapter_frames(id)
                })
        return chapters

    def run(self):
        language = self.manifest.target_language['id']
        chapters = self.get_chapters()

        for chapter in chapters:
            markdown = '# {0}\n\n'.format(chapter.get('title'))
            for frame in chapter.get('frames'):
                markdown += '![Frame {0}](https://cdn.door43.org/obs/jpg/360px/obs-en-{0}.jpg)\n\n'.format(frame.get('id'))
                markdown += frame.get('text')+'\n\n'
            markdown += '_{0}_\n'.format(chapter.get('reference'))

            output_file = os.path.join(self.output_dir, '{0}.md'.format(chapter.get('id')))
            write_file(output_file, markdown)


class TsBibleUsfmPreprocessor(UsfmPreprocessor):
    def __init__(self, *args, **kwargs):
        super(TsBibleUsfmPreprocessor, self).__init__(*args, **kwargs)
        self.title = ''

    def get_usfm_header(self):
        header = '\\id {0} {1}\n'.format(self.manifest.project['id'].upper(), self.manifest.resource['name'])
        header += '\\ide UTF-8\n'
        header += '\\h {0}\n'.format(self.title)
        header += '\\toc1 {0}\n'.format(self.title)
        header += '\\toc2 {0}\n'.format(self.title)
        header += '\\mt {0}\n\n'.format(self.title)
        return header

    def get_chapters(self):
        chapters = {}
        for root, dirnames, filenames in os.walk(self.source_dir):
            for filename in fnmatch.filter(filenames, '[0-9]*.txt'):
                chapter_key = os.path.basename(os.path.normpath(root))
                if chapter_key not in chapters:
                    chapters[chapter_key] = []
                chapters[chapter_key].append(os.path.join(root, filename))
        return chapters

    def get_chapter(self, key, chapter):
        chapter_content = '\\c ' + key + '\n' # put in chapter number
        for chapter in sorted(chapter):
            chapter_content += read_file(chapter) + '\n'
        return chapter_content + '\n\n'


    def get_title(self):
        """ Get the title of the project"""
        for root, dirnames, filenames in os.walk(self.source_dir):
            for filename in fnmatch.filter(filenames, 'title.txt'):
                return read_file(os.path.join(root, filename))
        return self.manifest.project['name']

    def run(self):
        self.title = self.get_title()
        usfm_content = self.get_usfm_header()

        chapters = self.get_chapters()

        for key in sorted(chapters):
            usfm_content += self.get_chapter(key, chapters[key])

        usfm_file = os.path.join(self.output_dir, '{0}-{1}.usfm'.format(bible_books.BOOK_NUMBERS[self.manifest.project['id']], self.manifest.project['id'].upper()))
        write_file(usfm_file, usfm_content)