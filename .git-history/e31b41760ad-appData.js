// @flow
import buildExperimentsClients from 'app/common/lib/buildExperimentsClients';
import fetchRouteData from 'node/handlers/utils/react/data/fetchRouteData';
import getRenderError from 'node/handlers/utils/react/data/getRenderError';
import getRouteData from 'shared/routing/getRouteData';
import getRoutes from 'shared/routing/getRoutes';
import populateStore from 'node/handlers/utils/react/data/populateStore';
import type { Metadata } from 'node/lib/Metatags';
import type { State } from 'app/common/redux/types';
import wrappedMatch from 'node/handlers/utils/react/wrappedMatch';
import { forEach } from 'lodash';
import { log } from 'node/util/Logger';
import { statClient } from 'node/lib/StatClient';
import getRouteBundles, { getRouteChunkFilenames } from 'node/handlers/utils/react/data/getRouteBundles';
import { errorCodeToString, ErrorCodes } from 'node/lib/Errors';

type ResponseData =
  | {
      status: 'success',
      store: State,
      page_metadata: ?{
        name: string,
        options?: Object,
        response: { data: Metadata, error: any },
        nextBookmark: string,
      },
      redirect: ?string,
      bundles: string[],
      error?: { statusCode?: number, message?: string, props?: Object },
    }
  | {
      status: 'redirect',
      redirect: string,
    }
  | {
      status: 'failure',
      message: string,
    };
type Response = {
  setHeader: (name: string, value: string) => void,
  charSet: (charSet: string) => void,
  send: (statusCode: number, data: ResponseData) => void,
};

export async function appData(request: Object, response: Response, next: Function) {
  response.setHeader('content-type', 'text/plain');
  response.charSet('utf-8');
  const pathname = request.url.substring(9);
  const query = JSON.parse(request.params.query);
  log.info(`[React] Constructing app data for ${pathname}...`);

  const { legacy_server_context } = request;
  const routes = getRoutes(legacy_server_context);
  const experimentsClients = buildExperimentsClients(legacy_server_context);

  // Defaulting status code to 500 because if we don't run into any of the if cases we end in error
  let statusCode = 500;

  try {
    const dataProps = await wrappedMatch({
      location: {
        pathname,
        query,
      },
      routes,
      legacy_server_context,
      experimentsClients,
    });

    const routeData = await getRouteData(dataProps, legacy_server_context);

    let appData;
    try {
      appData = await fetchRouteData({
        routeData,
        legacy_server_context,
        params: dataProps.params,
        experimentsClients,
      });
    } catch (error) {
      // If resource calls fail, render with empty data
      appData = {
        resourceResponses: [],
        metatagsResponse: null,
        redirect: null,
      };
      // TODO(jchan): Catch Promise.all errors individually, return array of rejected promises alongside successes
      log.info(`[React] Error fetching resources and metatags for ${pathname} - appData endpoint: ${error}`);
      log.error(`[React] Route match for ${pathname} failed - appData endpoint.`, {
        error,
        request,
        context: legacy_server_context,
        code: errorCodeToString(ErrorCodes.REACT_APP_DATA_RESOURCE_FETCH_ERROR),
      });
    }

    const { metatagsResponse, resourceResponses, redirect } = appData;

    const renderError = getRenderError(
      routeData,
      legacy_server_context,
      dataProps,
      resourceResponses,
      pathname,
      request,
    );

    statusCode = 200;
    response.send(statusCode, {
      status: 'success',
      store: populateStore(routeData, resourceResponses, legacy_server_context, dataProps, renderError).getState(),
      page_metadata: metatagsResponse,
      redirect,
      bundles: getRouteBundles(dataProps),
      chunkFilenames: getRouteChunkFilenames(dataProps),
      upwtActionName: routeData.upwtActionName,
    });
    log.info(`[React] 200 - Data constructed for ${pathname}`);
  } catch (error) {
    if (error.statusCode) {
      statusCode = error.statusCode;
    }
    if (statusCode === 301) {
      response.send(statusCode, {
        status: 'redirect',
        redirect: error.location,
      });
      log.info(`[React] ${statusCode} - Redirecting ${pathname} to ${error.location}`);
    } else if (statusCode === 404) {
      response.send(statusCode, {
        status: 'failure',
        message: 'Not found',
      });
      log.info(`[React] ${statusCode} - No route match for ${pathname} - appData endpoint`);
      log.error(`[React] Route match for ${pathname} failed - appData endpoint.`, {
        error,
        request,
        context: legacy_server_context,
        code: errorCodeToString(ErrorCodes.REACT_ROUTER_MATCH_NOT_FOUND),
      });
    } else {
      response.send(statusCode, {
        status: 'failure',
        message: 'Error',
      });
      log.info(`[React] ${statusCode} - Error in constructing data for ${pathname}`);
      log.error(`[React] Constructing data for ${pathname} failed`, {
        error,
        request,
        context: legacy_server_context,
        code: errorCodeToString(ErrorCodes.REACT_APP_DATA_ERROR),
      });
    }
  }

  statClient.increment(`ngjs.reactAppData.sentResponse.${statusCode}`);
  next();
  // Flush side effects
  forEach(experimentsClients, (experimentClient) => {
    experimentClient.flush_changes(legacy_server_context);
  });
}

export default undefined;
