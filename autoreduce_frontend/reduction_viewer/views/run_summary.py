import logging
from autoreduce_db.reduction_viewer.models import ReductionRun
from autoreduce_frontend.autoreduce_webapp.view_utils import (check_permissions, login_and_uows_valid, render_with)

from autoreduce_frontend.plotting.plot_handler import PlotHandler
from autoreduce_frontend.reduction_viewer.views.common import get_arguments_from_run
from autoreduce_frontend.reduction_viewer.view_utils import (get_interactive_plot_data, linux_to_windows_path,
                                                             make_data_analysis_url, windows_to_linux_path,
                                                             started_by_id_to_name)

LOGGER = logging.getLogger(__package__)


@login_and_uows_valid
@check_permissions
@render_with('run_summary.html')
# pylint:disable=no-member,too-many-locals,broad-except
def run_summary(request, instrument_name=None, run_number=None, run_version=0):
    """Render run summary."""
    history = ReductionRun.objects.filter(instrument__name=instrument_name,
                                          batch_run=False,
                                          run_numbers__run_number=run_number).order_by('-run_version').select_related(
                                              'status').select_related('experiment').select_related('instrument')
    if len(history) == 0:
        raise ValueError(f"Could not find any matching runs for instrument {instrument_name} run {run_number}")

    return run_summary_run(request, history, instrument_name, run_version)


@login_and_uows_valid
@check_permissions
@render_with('run_summary.html')
# pylint:disable=no-member,too-many-locals,broad-except
def run_summary_batch_run(request, instrument_name=None, pk=None, run_version=0):
    """Gathers the context and renders a run's summary"""
    history = ReductionRun.objects.filter(instrument__name=instrument_name, pk=pk).order_by(
        '-run_version').select_related('status').select_related('experiment').select_related('instrument')
    if len(history) == 0:
        raise ValueError(f"Could not find any matching runs for instrument {instrument_name} run {pk}")

    return run_summary_run(request, history, instrument_name, run_version)


def run_summary_run(request, history, instrument_name=None, run_version=0):
    """Gathers the context and renders a run's summary"""
    run = next(run for run in history if run.run_version == int(run_version))
    started_by = started_by_id_to_name(run.started_by)

    # Run status value of "s" means the run is skipped
    is_skipped = run.status.value == "s"
    is_rerun = len(history) > 1

    location_list = run.reduction_location.all()
    reduction_location = ""
    if location_list:
        reduction_location = location_list[0].file_path
    if reduction_location and '\\' in reduction_location:
        reduction_location = reduction_location.replace('\\', '/')

    data_location_list = run.data_location.all()
    data_location = ""
    if data_location_list:
        data_location = data_location_list[0].file_path
        print(data_location)

    path_type = request.GET.get('path_type', "")
    if path_type == "linux":
        data_location = windows_to_linux_path(data_location)
    elif path_type == "windows":
        data_location = linux_to_windows_path(data_location)

    data_analysis_link_url = make_data_analysis_url(reduction_location) if reduction_location else ""
    rb_number = run.experiment.reference_number
    standard_vars, advanced_vars, variable_help = get_arguments_from_run(run)

    run_number = run.pk if run.batch_run else run.run_number

    context_dictionary = {
        'run': run,
        'run_number': run_number,
        'run_version': run_version,
        'has_reduce_vars': bool(standard_vars),
        'batch_run': run.batch_run,
        'standard_variables': standard_vars,
        'advanced_variables': advanced_vars,
        'variable_help': variable_help,
        'instrument': instrument_name,
        'is_skipped': is_skipped,
        'is_rerun': is_rerun,
        'history': history,
        'data_location': data_location,
        'reduction_location': reduction_location,
        'started_by': started_by,
        'data_analysis_link_url': data_analysis_link_url,
        'current_page': int(request.GET.get('page', 1)),
        'items_per_page': int(request.GET.get('pagination', 10)),
        'page_type': request.GET.get('sort', 'run'),
        'newest_run': int(request.GET.get('newest_run', run_number)),
        'oldest_run': int(request.GET.get('oldest_run', run_number)),
        'next_run': int(request.GET.get('next_run', run_number)),
        'previous_run': int(request.GET.get('previous_run', run_number)),
        'filtering': request.GET.get('filter', 'run'),
        'new_path_type': 'windows' if path_type == 'windows' else 'linux',
    }

    if reduction_location:
        try:
            plot_handler = PlotHandler(data_filepath=run.data_location.first().file_path,
                                       server_dir=reduction_location,
                                       rb_number=rb_number)
            local_plot_locs, server_plot_locs = plot_handler.get_plot_file()
            if local_plot_locs:
                context_dictionary['static_plots'] = [
                    location for location in local_plot_locs if not location.endswith(".json")
                ]

                context_dictionary['interactive_plots'] = get_interactive_plot_data(server_plot_locs)
        except Exception as exception:
            # Lack of plot images is recoverable - we shouldn't stop the whole
            # page rendering if something is wrong with the plot images - but
            # display an error message
            err_msg = "Encountered error while retrieving plots for this run"
            LOGGER.error("%s. Instrument: %s, run %s. RB Number %s Error: %s", err_msg, run.instrument.name, run,
                         rb_number, exception)
            context_dictionary["plot_error_message"] = f"{err_msg}."

    return context_dictionary