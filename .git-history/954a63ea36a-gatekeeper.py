from collections import defaultdict
import logging

from common.utils.time_utils import to_seconds
from common.utils import iter_utils
from config import seo_experiments
from core.gatekeeper.experiment import get_experiments
from core.gatekeeper.user_experiments import get_user_experiments
from core.gatekeeper.user_experiments import log_user_experiments
from logger.statsd import stat_client_v2
from schemas.experiment_if.ttypes import ExperimentUserSessionInfo
import settings

logger = logging.getLogger(__name__)


class Gatekeeper(object):
    """Experiments v2 Gatekeeper. It wraps two methods: ``get_user_experiments`` and ``log_user_experiments``.
    It will manage state around activated experiments.

    Usage:

    >>> import core.gatekeeper as gk

    # Create the Gatekeeper instance with a context
    >>> gatekeeper = gk.Gatekeeper(gk.GatekeeperContext(1234569))

    # Check for the experiment eligible group.
    >>> gatekeeper.get_group('MyExp')
    'control'
    >>> gatekeeper.get_group('OtherExp') in ('a', 'b')
    True

    # Activate the experiment. This will log that the user seen the group's treatment
    >>> gatekeeper.activate_experiment('MyExp')
    >>> gatekeeper.activate_experiment('OtherExp', override_group='b')  # Force 'b'

    # Log any activated experiments.
    >>> gatekeeper.log_experiments()

    """

    def __init__(self, context=None, override_experiments_config=None,
                 forced_experiments=None, no_experiments=False,
                 batched_logging=False, limited_experiments=None):
        """Initialize Gatekeeper.

        Args:
            ``context``:
                A ``GatekeeperContext`` instance.
            ``override_experiments_config``:
                A list of experiment objects which will override experiment config.
                If omitted default config from ALL_EXPERIMENTS will be used.
            ``batched_logging``:
                Whether to defer logging called in batch for better performance,
                setting batch_logging=True will require log_experiments called by explicitly.
            ``limited_experiments``:
                A list of experiment keys to include.
                If set to non-empty list, the gatekeeper will evaluate only these experiments,
                rather than the entire set of experiments in the config.
                If set to non-empty list, group will be None for experiments not in the list.
        """
        self.context = context
        self.override_experiments_config = override_experiments_config
        self.forced_experiments = forced_experiments
        self.no_experiments = no_experiments
        self.batched_logging = batched_logging
        self.limited_experiments = limited_experiments

        self._activated_experiments = defaultdict(list)
        self._all_activated_experiments = defaultdict(list)

        if settings.FORCED_EXPERIMENTS:
            if self.forced_experiments:
                self.forced_experiments.update(settings.FORCED_EXPERIMENTS)
            else:
                self.forced_experiments = settings.FORCED_EXPERIMENTS

    def get_group(self, experiment_name):
        """Get the group the user belongs to in a given experiment.
           Returns the group name or None if the user isn't in the experiment.
        """
        experiment = self._get_user_experiment_with_name(experiment_name)
        return experiment.get('group', None)

    def activate_experiment(self, experiment_name, override_group=None):
        """Activate the experiment by putting experiment into _activated_experiments.

        Args:
            ``experiment_name``:
                The name of the experiment to activate.
            ``override_group``:
                If specified, use this as the active group.
        """
        experiment = self._get_user_experiment_with_name(experiment_name)

        # No need to log if there's no eligible experiment and no override group.
        if not experiment and not override_group:
            return None

        experiment_group = override_group or experiment.get('group')
        experiment_version = experiment.get('version', 1)
        exp_info = {
            'group': experiment_group,
            'version': experiment_version}
        self._activated_experiments[experiment_name].append(exp_info)
        self._all_activated_experiments[experiment_name].append(exp_info)

        experiment_stats_key = "%s.%s.%s" % (experiment_name, experiment_version, experiment_group)
        tags = {'exp_stats_key': experiment_stats_key}
        stat_client_v2.increment('gk.activate', sample_rate=0.01, tags=tags)

        # Log immediately when activation get called for non batched logging.
        if not self.batched_logging:
            log_user_experiments(self.context, {experiment_name: [{
                'group': experiment_group,
                'version': experiment_version}]})
        return experiment_group

    def _get_forced_group(self, experiment_name):
        """Returns the forced experiment group for this experiment_name. Please avoid using this method directly.
        It is here mainly for allowing SEO experiments override.
        """
        if self.forced_experiments:
            return self.forced_experiments.get(experiment_name)
        return None

    def activate_seo_or_unauth_experiment(self, experiment_name, override_unique_id=None, skip_logging=False):
        """V2 API for activating unauth experiment or getting SEO experiment group, depends on the viewer.
        In V2, an SEO experiment is usually coupled with another unauth experiment, the difference is the name of
        the SEO experiment has an 'seo_' prefix. This API will decide which type of experiment (seo or unauth)
        based on the viewer from the context information and activate the corresponding one.

        Args:
            ``experiment_name``:
                The name of the experiment to activate.
            ``override_unique_id``:
                If specified, use this to override the unique_id, usually this is a webapp_url for SEO experiment.
        """
        # Check if this is for an SEO experiment
        if self.context.get('is_bot'):
            # For SEO experiment, we compute the group here
            seo_experiment_name = 'seo_' + experiment_name

            # Allow SEO experiment override
            group = self._get_forced_group(seo_experiment_name) or self._get_forced_group(experiment_name)
            if group:
                return group

            unique_id = override_unique_id or self.context.get('webapp_url', None)
            if not unique_id:
                return None
            group = seo_experiments.get_experiment_group(seo_experiment_name, unique_id=unique_id,
                                                         skip_logging=skip_logging)
            if not group:
                return None
            # Log immediately when activation get called for non batched logging.
            self.context.info['seo_unique_id'] = unique_id
            if not skip_logging:
                log_user_experiments(self.context, {seo_experiment_name: [{
                    'group': group,
                    'version': 1}]})
            return group
        else:
            return self.activate_experiment(experiment_name)

    def get_seo_or_unauth_experiment_group(self, experiment_name):
        """
        Get the experiment group for an unauth session, either a SEO experiment for a bot or an unauth experiment for an
        unauth user.
        :param experiment_name:
        :return experiment_group or None:
        """
        if self.context.get('is_bot'):
            return self.activate_seo_or_unauth_experiment(experiment_name, skip_logging=True)
        else:
            return self.get_group(experiment_name)

    def log_experiments(self):
        """Save and log any activated experiments and clear existing activated experiments."""
        if self._activated_experiments:
            log_user_experiments(self.context, self._activated_experiments)

        # Flush the activated experiments
        self._activated_experiments = defaultdict(list)

    def get_experiments(self):
        """Return all experiment_name: experiment_group pairs associated with the context,
        both activated and inactivated.
        """
        user_experiments = get_user_experiments(self.context,
                                                override_experiments_config=self.override_experiments_config,
                                                limited_experiments=self.limited_experiments,
                                                forced_experiments=self.forced_experiments,
                                                no_experiments=self.no_experiments)
        experiments = {name: {
            'group': experiment.get('group', None),
            'key': name} for name, experiment in user_experiments.iteritems()}

        for name, exp_infos in self._activated_experiments:
            if not exp_infos:
                continue
            experiments[name] = exp_infos[0].get('group', None)

        return experiments

    def get_experiments_config(self):
        """Return all experiment definitions associated with the context,
        both activated and inactivated.
        """
        user_experiments = get_user_experiments(self.context,
                                                override_experiments_config=self.override_experiments_config,
                                                limited_experiments=self.limited_experiments,
                                                forced_experiments=self.forced_experiments,
                                                no_experiments=self.no_experiments)
        experiments = {name: {
            'group': experiment.get('group', None),
            'key': name} for name, experiment in user_experiments.iteritems()}

        for name, exp_infos in self._activated_experiments:
            if not exp_infos:
                continue
            experiments[name] = exp_infos[0].get('group', None)

        all_configs = {}
        for key, experiment in get_experiments().iteritems():
            value = experiments.get(key, {})
            value['dict_data'] = experiment.dict_data
            all_configs[key] = value
        return all_configs

    def _get_all_activated_experiments(self):
        """Returns all activated experiments from this gatekeeper. Please avoid using this method directly.
        It is here mainly for providing access to activated experiments for performance timing purposes.
        """
        return {name: exp_infos[0] for name, exp_infos in self._all_activated_experiments.iteritems() if exp_infos}

    def _get_user_experiment_with_name(self, experiment_name):
        user_experiments = get_user_experiments(context=self.context,
                                                override_experiments_config=self.override_experiments_config,
                                                limited_experiments=self.limited_experiments or [experiment_name],
                                                forced_experiments=self.forced_experiments,
                                                no_experiments=self.no_experiments)
        return user_experiments.get(experiment_name, {})

    def get_experiment_user_session_info(self):
        if self.context.user and self.context.user.is_authenticated():
            return _get_experiment_user_session_info_for_auth(self.context,
                                                              self.forced_experiments,
                                                              self.no_experiments)
        else:
            # TODO(experiments v2 team): Fix ExperimentUserSessionInfo so that uniqueId can be a string.
            return _get_experiment_user_session_info_for_unauth(self.context,
                                                                self.forced_experiments,
                                                                self.no_experiments)

    def get_gk_context_data(self):
        """
        Returns a dictionary of values from the GatekeeperContext object minus the user object.
        """
        info_dict = self.context.info.copy()

        if 'user' in info_dict:
            del info_dict['user']

        # Add the unique ID passed into the context for debugging
        info_dict['unique_id'] = self.context.unique_id

        return info_dict


def _get_experiment_user_session_info_for_unauth(context, forced_experiments, no_experiments):
    return ExperimentUserSessionInfo(
        uniqueId=0L,
        sessId=context.get('sessid'),
        locale=context.get('locale'),
        country=context.get('country'),
        isBot=context.get('is_bot'),
        ipAddress=context.get('ip_address'),
        isInternalIp=context.get('is_internal_ip'),
        referrer=context.get('referrer'),
        userAgent=context.get('user_agent'),
        acceptLang=context.get('accept_lang'),
        appType=context.get('app_type'),
        appVersion=context.get('app_version'),
        device=None,
        forceExperiments=forced_experiments,
        forceNoExperiments=no_experiments,
    )


def _get_experiment_user_session_info_for_auth(context, forced_experiments, no_experiments):
    return ExperimentUserSessionInfo(
        uniqueId=context.unique_id,
        sessId=context.get('sessid'),
        locale=context.get('locale'),
        country=context.user.get('country'),
        isBot=context.get('is_bot'),
        ipAddress=context.get('ip_address'),
        isInternalIp=context.get('is_internal_ip'),
        referrer=context.get('referrer'),
        userAgent=context.get('user_agent'),
        acceptLang=context.get('accept_lang'),
        appType=context.get('app_type'),
        appVersion=context.get('app_version'),

        # TODO(experiments v2/data-eng): context.get('device') is a raw header string, not a DeviceType. That's
        # incompatible with the Thrift definition of ExperimentUserSessionInfo.
        # Suggested fix: populate context['device'] with request_context.parsed_ua.device_type (DeviceType) instead of
        # the X-Pinterest-Device header string. This needs to be fixed in GatekeeperContext.from_api_context
        # and api/gatekeeper.py#_get_gatekeeper_v2.
        device=None,

        isEmployee=context.user.is_employee,
        gender=context.user.gender,
        forceExperiments=forced_experiments,
        forceNoExperiments=no_experiments,
        firstName=context.user.first_name.encode('utf-8') if hasattr(context.user, 'created_at')else None,
        lastName=context.user.last_name.encode('utf-8') if hasattr(context.user, 'created_at') else None,
        userName=context.user.username,
        lodestone=context.unique_id in settings.LODESTONE_TEST_ACCOUNTS,
        localizationQa=context.unique_id in settings.LOCALIZATION_QA_ACCOUNTS,
        appleDevrel=context.unique_id in settings.APPLE_DEVREL_ACCOUNTS,
        integrationTest=context.unique_id in settings.INTEGRATION_TEST_ACCOUNTS,
        userJoinDate=to_seconds(context.user.created_at) if getattr(context.user, 'created_at', None) else None
    )


class MemoizedGatekeeper(Gatekeeper):
    """Gatekeeper that memoizes results. Useful if you query the same few experiments many times"""

    def __init__(self, *args, **kwargs):
        super(MemoizedGatekeeper, self).__init__(*args, **kwargs)
        self._experiment_groups = dict()
        self._activated_groups = dict()

    def get_group(self, experiment_name):
        if experiment_name not in self._experiment_groups:
            self._experiment_groups[experiment_name] = super(MemoizedGatekeeper, self).get_group(experiment_name)
        return self._experiment_groups[experiment_name]

    def activate_experiment(self, experiment_name, override_group=None):
        if override_group:
            super(MemoizedGatekeeper, self).activate_experiment(experiment_name, override_group=override_group)
            return override_group
        if experiment_name not in self._activated_groups:
            self._activated_groups[experiment_name] = super(MemoizedGatekeeper, self).activate_experiment(
                experiment_name, override_group=override_group)
        return self._activated_groups[experiment_name]

    def clear_cache(self):
        self._experiment_groups.clear()
        self._activated_groups.clear()
