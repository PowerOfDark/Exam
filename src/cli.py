import click
import sys
import os
import related
import statistics
from models import ProblemSet, Exam, SchemeError
from utils import get_params, percentage, short_str
from graders import GRADERS
from matplotlib import pyplot as plt
import numpy as np


COMMANDS_WITHOUT_PROBLEM_SET = {
    'create-problem-set',
    'open-exam'
}  # define commands that don't require a problem set


def require_meta(obj: ProblemSet):
    """
    Raises an error if the problem set wasn't provided
    """
    if obj is None:
        raise click.BadOptionUsage("problem_set",
                                   "Unspecified problem set (use --problem-set=PATH)")


def save_meta(obj: ProblemSet):
    """
    Saves the problem set into its import location
    """
    if obj:
        obj.save(obj.source)
        click.echo(f"Problem set `{obj.title}` saved to {obj.source}")


def load_exam(path: str) -> Exam:
    """
    Attempts to deserialize an Exam from the given file path
    """
    try:
        with open(path, 'r') as file:
            exam = related.from_yaml(file, Exam)
            return exam
    except Exception as ex:
        raise click.ClickException(f"Invalid exam file `{path}` ({ex})") from ex


@click.group()
@click.option('--problem-set', '-s', metavar='PATH', required=False, type=click.Path(exists=True),
              help='Path to the problem set')
@click.pass_context
def cli(ctx, problem_set):
    # Ran before any command; imports the problem set
    ctx.obj = None
    if problem_set:
        try:
            meta = ProblemSet.from_file(problem_set)
            ctx.obj = meta
            meta.source = problem_set
        except Exception as ex:
            raise click.ClickException(f"Invalid problem set `{problem_set}` ({ex})") from ex
    elif ctx.invoked_subcommand not in COMMANDS_WITHOUT_PROBLEM_SET:
        if '--help' not in sys.argv:  # check if 'help' requested
            require_meta(ctx.obj)


@cli.command()
@click.option('--path', '-p', prompt='Path (*.yml)', type=click.Path(), help='Export path')
@click.option('--title', '-t', prompt=True, type=click.STRING, help='Name of the problem set')
def create_problem_set(path, title):
    """
    Creates an empty problem set
    """
    meta = ProblemSet(title=title)
    meta.save(path)
    click.echo(f"Successfully created problem set in {path}")


@cli.command()
@click.option('--num-answers', '-a', default=None, type=click.INT)
@click.option('--num-correct-answers', '-c', default=None, type=click.INT)
@click.option('--points', '-p', default=None, type=click.INT)
@click.option('--grader', '-g', default=None, type=click.Choice(list(GRADERS.keys())))
@click.option('--likelihood', '-l', default=None, type=click.INT)
@click.option('--is-multiple-choice', '-m', default=None, type=click.BOOL)
@click.pass_obj
def edit_defaults(meta, answers, correct_answers, points, grader, likelihood, is_multiple_choice):
    """
    Modifies problem set defaults for unspecified properties when creating new questions
    """
    qd = meta.question_defaults
    if answers:
        qd.num_answers = answers
    if correct_answers:
        qd.num_correct_answers = answers
    if points:
        qd.points = points
    if grader:
        qd.grader = grader
    if likelihood:
        qd.likelihood = likelihood
    if is_multiple_choice:
        qd.is_multiple_choice = is_multiple_choice

    save_meta(meta)

    click.echo("New defaults -")
    click.echo(related.to_yaml(qd))


def add_question_id(ctx: click.Context, param, value):
    meta = ctx.obj
    id = value
    if id:
        question = meta.find_question(id)
        if question:
            raise click.ClickException(
                "Question with specified ID already exists. Did you mean to use `edit-question`?")
    return value


@cli.command()
@click.pass_obj
@click.option('--id', '-i', prompt=True, type=click.STRING, callback=add_question_id)
@click.option('--text', '-t', default=None, type=click.STRING)
@click.option('--num-answers', '-a', default=None, type=click.INT)
@click.option('--num-correct-answers', '-c', default=None, type=click.INT)
@click.option('--points', '-p', default=None, type=click.INT)
@click.option('--grader', '-g', default=None, type=click.Choice(list(GRADERS.keys())))
@click.option('--likelihood', '-l', default=None, type=click.INT)
@click.option('--is-multiple-choice', '-m', default=None, type=click.BOOL)
def add_question(meta, id, **kwargs):
    """
    Adds a question to the problem set
    """

    args = get_params(**kwargs)
    try:
        meta.insert_question(False, id, **args)
    except KeyError as ex:
        raise click.ClickException("Invalid question ID") from ex

    click.echo(f"Question `{id}` added successfully")
    save_meta(meta)


def edit_question_id(ctx: click.Context, param, value):
    meta = ctx.obj
    require_meta(meta)
    id = value
    question = meta.find_question(id)
    if question is None:
        raise click.ClickException("Question with specified ID was not found")
    return value


@cli.command()   # I'd love to avoid copying this block of parameters
@click.pass_obj  # https://click.palletsprojects.com/en/7.x/why/#why-hardcoded-behaviors
@click.option('--id', '-i', prompt=True, type=click.STRING, callback=edit_question_id)
@click.option('--text', '-t', default=None, type=click.STRING)
@click.option('--num-answers', '-a', default=None, type=click.INT)
@click.option('--num-correct-answers', '-c', default=None, type=click.INT)
@click.option('--points', '-p', default=None, type=click.INT)
@click.option('--grader', '-g', default=None, type=click.Choice(list(GRADERS.keys())))
@click.option('--likelihood', '-l', default=None, type=click.INT)
@click.option('--is-multiple-choice', '-m', default=None, type=click.BOOL)
def edit_question(meta, id, **kwargs):
    """
    Edits an existing question
    """

    args = get_params(**kwargs)
    meta.insert_question(True, id, **args)

    click.echo(f"Question `{id}` updated successfully")
    save_meta(meta)


@cli.command()
@click.pass_obj
@click.argument('id', type=click.STRING)
@click.option('--format', '-f', default='yaml', type=click.Choice(['yaml', 'json']))
def get_question(meta, id, format):
    """
    Dumps a question in the specified format
    """

    question = meta.find_question(id)
    if question is None:
        raise click.ClickException("Question with specified ID was not found")

    text = ''
    if format == 'json':
        text = related.to_json(question)
    else:
        text = related.to_yaml(question)

    click.echo(text)


@cli.command()
@click.pass_obj
@click.option('--id', '-i', default=None, required=False, multiple=True, type=click.STRING)
@click.option('--hide-answers', '-h', is_flag=True, type=click.BOOL)
def list_questions(meta, id, hide_answers):
    """
    Lists all questions in the problem set
    """

    for qid, question in meta.questions.items():
        if len(id) == 0 or qid in id:
            click.echo(f"{qid}: {question.text}")
            if not hide_answers:
                for ans in question.answers:
                    click.echo(f"\t{ans}")

    click.echo(f"Processed {len(meta.questions)} question(s)")


def add_answer_qid(ctx, param, value):
    meta = ctx.obj
    id = value
    question = meta.find_question(id)
    if question is None:
        click.echo("Question with specified ID not found")
        ctx.abort()
    else:
        click.echo(question.text)

    return value


@cli.command()
@click.pass_obj
@click.option('--question-id', '-q', prompt=True, type=click.STRING, callback=add_answer_qid)
@click.option('--text', '-t', prompt=True, type=click.STRING)
@click.option('--correct', '-c', default=None, type=click.BOOL)
@click.option('--likelihood', '-l', default=1, type=click.INT)
@click.option('--id', '-i', default=None, type=click.INT)
def add_answer(meta, question_id, text, correct, likelihood, id):
    """
    Adds (or modifies) an answer to a question in problem set
    """

    optional = get_params(is_correct=correct)
    question = meta.find_question(question_id)
    question.insert_answer(id, text=text, likelihood=likelihood, **optional)

    click.echo(f"Answer `{id}` updated successfully")
    save_meta(meta)


@cli.command()
@click.pass_obj
@click.option('--title', '-t', prompt=True, type=click.STRING)
@click.option('--description', '-d', prompt=True, type=click.STRING)
@click.option('--num-questions', '-n', prompt=True, type=click.INT)
@click.option('--path', '-p', prompt="Path (*.yml)", type=click.Path(dir_okay=False))
def gen_exam(meta, title, description, num_questions, path):
    """
    Generates an exam file
    """

    try:
        exam = meta.generate_exam(num_questions, description, title)
        exam.save(path)
        click.echo(f"Exam written to {path}")
    except Exception as ex:
        raise click.ClickException(f"Could not generate an exam ({ex})") from ex


@cli.command()
@click.pass_obj
@click.argument('exam', required=True, type=click.Path(exists=True))
@click.option('--clear', required=False, is_flag=True, type=click.BOOL)
def open_exam(meta, exam, clear):
    """
    Provides a GUI to interact with the exam file.
    Specify `--problem-set` to automatically grade the answers.
    """
    exam_obj = load_exam(exam)

    if meta:
        try:
            meta.ensure_exam_compatibility(exam_obj)
        except SchemeError as ex:
            raise click.ClickException(f"{ex}") from ex

    if clear:
        exam.clear()

    # clear CLI args
    sys.argv = [sys.argv[0]]

    # run UI
    from ui.exam import ExamApp
    app = ExamApp(meta, exam_obj, exam)
    app.run()


def grade_exam(meta, path, question_callback) -> (int, int, float, str):
    """
    Utility function that grades a single exam
    Returns
        A tuple of (score, max_score, percentage, user_name)
    """
    try:
        exam = load_exam(path)
        if not exam.was_user_completed:
            raise Exception('Not completed')
        meta.ensure_exam_compatibility(exam)
        score = exam.get_score(meta, question_callback)
        max_score = exam.max_score
        percent = percentage(score, max_score)
        return score, max_score, percent, exam.user_name
    except Exception as ex:
        click.echo(f"{os.path.basename(path)}: {ex}")
    return None


def format_score(score, max_score) -> str:
    percent = percentage(score, max_score)
    return f"{score:.1f} / {max_score:.1f} ({percent:.1f}%)"


def display_user_stats(user_scores):
    # order by score percentage
    click.echo("Per-user score stats:")
    scores = user_scores.items()
    # user, (score, max_score, percentage) -> x[1][2]
    ordered = sorted(scores, key=lambda x: x[1][2], reverse=True)

    for i, (user, pair) in enumerate(ordered):
        click.echo(f"{i + 1}. {user}: {format_score(pair[0], pair[1])}")
    click.echo()


def display_question_stats(meta, question_stats):
    # format as:
    # question (question id)
    #   [0p]: 1 (10%)
    #   [1p]: 9 (90%)
    TEXT_LENGTH = 32
    click.echo("Per-question score stats:")
    for qid, scores in question_stats.items():
        question = meta.find_question(qid)
        click.echo(f"{short_str(question.text, TEXT_LENGTH)} ({qid})")
        total = sum(count for score, count in scores.items())
        for score, count in scores.items():
            percent = percentage(count, total)
            click.echo(f"\t[{score}p]: {count} ({percent:.1f}%)")
        click.echo()
    click.echo()


def display_plot(scores, max_score):
    stats = plt.hist(scores, label='Exam scores', range=(0, max_score))
    plt.xlabel('Combined score')
    plt.ylabel('Participants')
    plt.xticks(stats[1])  # sets the histogram bin intervals as X-axis labels
    plt.yticks(np.arange(0, len(scores), 1.0))
    plt.title('Exam scores')
    plt.show()


def display_general_stats(scores, max_score, plot=False):
    click.echo(f"Number of participants: {len(scores)}")
    mean = statistics.mean(scores)
    click.echo(f"Mean score: {format_score(mean, max_score)}")
    median = statistics.median(scores)
    click.echo(f"Median score: {format_score(median, max_score)}")
    # show the plot
    if plot:
        display_plot(scores, max_score)


@cli.command()
@click.pass_obj
@click.argument('directory', type=click.Path(exists=True, file_okay=False, dir_okay=True))
@click.option('--plot', '-p', is_flag=True, type=click.BOOL, help="Plot scores using matplotlib")
@click.option('--display-questions', '-q', is_flag=True, type=click.BOOL,
              help="Display question stats")
def grade_exams(meta, directory, plot, display_questions):
    """Grades all exams in the given directory"""
    user_scores = dict()     # stores user scores
    question_stats = dict()  # counts scores per-question
    max_score = 0

    def on_question(question, score):
        # handle a graded question
        nonlocal question_stats
        qid = question.id
        map = question_stats.get(qid, dict())
        map[score] = map.get(score, 0) + 1  # +1 occurrence
        question_stats[qid] = map

    # grade all files in the folder; show a progress bar
    with click.progressbar(os.listdir(directory)) as files:
        for file in files:
            path = os.path.join(directory, file)
            output = grade_exam(meta, path, on_question)
            if output:
                *stats, user = output
                user_scores[user] = stats
                # get max score so far
                max_score = max(max_score, stats[1])

    if len(user_scores) == 0:
        click.echo('No valid exams found')
        return

    if display_questions:
        display_question_stats(meta, question_stats)
    display_user_stats(user_scores)
    display_general_stats([score for score, *_ in user_scores.values()], max_score, plot)
