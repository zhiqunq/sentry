import React from "react";
import Router from "react-router";
import api from "../../api";
import Count from "../../components/count";
import LoadingError from "../../components/loadingError";
import LoadingIndicator from "../../components/loadingIndicator";
import PropTypes from "../../proptypes";
import RouteMixin from "../../mixins/routeMixin";
import TimeSince from "../../components/timeSince";
import ProjectState from "../../mixins/projectState";

var EventNode = React.createClass({
  mixins: [ProjectState],

  propTypes: {
    group: PropTypes.Group.isRequired
  },

  makeGroupLink(title) {
    var group = this.props.group;
    var org = this.getOrganization();

    var params = {
      orgId: org.slug,
      projectId: group.project.slug,
      groupId: group.id
    };

    return (
      <Router.Link to="groupDetails" params={params}>
        {title}
      </Router.Link>
    );
  },

  render() {
    var group = this.props.group;

    var userCount = (group.tags["sentry:user"] !== undefined ?
      userCount = group.tags["sentry:user"].count :
      0);

    return (
      <li className="group">
        <div className="row">
          <div className="col-xs-8 event-details">
            <h3 className="truncate">{this.makeGroupLink(group.title)}</h3>
            <div className="event-message">{group.culprit}</div>
            <div className="event-extra">
              <ul>
                <li>
                  <span className="icon icon-clock"></span>
                  <TimeSince date={group.lastSeen} />
                  &nbsp;&mdash;&nbsp;
                  <TimeSince date={group.firstSeen} suffix="old" />
                </li>
              </ul>
            </div>
          </div>
          <div className="col-xs-2 event-count align-right">
            <Count value={group.count} />
          </div>
          <div className="col-xs-2 event-users align-right">
            <Count value={userCount} />
          </div>
        </div>
      </li>
    );
  }
});

var EventList = React.createClass({
  mixins: [
    RouteMixin
  ],

  contextTypes: {
    router: React.PropTypes.func
  },

  propTypes: {
    title: React.PropTypes.string.isRequired,
    endpoint: React.PropTypes.string.isRequired
  },

  getInitialState() {
    return {
      groupList: [],
      loading: true,
      error: false,
      statsPeriod: "24h"
    };
  },

  componentWillMount() {
    this.fetchData();
  },

  routeDidChange(nextPath, nextParams) {
    var router = this.context.router;
    var params = router.getCurrentParams();
    if (nextParams.teamId != params.teamId) {
      this.fetchData();
    }
  },

  componentDidUpdate(_, prevState) {
    if (this.state.statsPeriod != prevState.statsPeriod) {
      this.fetchData();
    }
  },

  fetchData() {
    this.setState({
      loading: true,
      error: false
    });

    var minutes;
    switch(this.state.statsPeriod) {
      case "15m":
        minutes = "15";
        break;
      case "60m":
        minutes = "60";
        break;
      case "24h":
        minutes = "1440";
        break;
    }

    api.request(this.props.endpoint, {
      query: {
        limit: 5,
        minutes: minutes
      },
      success: (data) => {
        this.setState({
          groupList: data,
          loading: false,
          error: false
        });
      },
      error: () => {
        this.setState({
          loading: false,
          error: true
        });
      }
    });
  },

  onSelectStatsPeriod(period) {
    this.setState({
      statsPeriod: period
    });
  },

  render() {
    var eventNodes = this.state.groupList.map((item) => {
      return <EventNode group={item} key={item.id} />;
    });

    return (
      <div className="box">
        <div className="box-header clearfix">
          <div className="row">
            <div className="col-xs-8">
              <h3>{this.props.title}</h3>
            </div>
            <div className="col-xs-2 align-right">Events</div>
            <div className="col-xs-2 align-right">Users</div>
          </div>
        </div>
        <div className="box-content">
          <div className="tab-pane active">
            {this.state.loading ?
              <LoadingIndicator />
            : (this.state.error ?
              <LoadingError onRetry={this.fetchData} />
            : (eventNodes.length ?
              <ul className="group-list group-list-small">
                {eventNodes}
              </ul>
            :
              <div className="group-list-empty">No data available.</div>
            ))}
          </div>
        </div>
      </div>
    );
  }
});

export default EventList;

