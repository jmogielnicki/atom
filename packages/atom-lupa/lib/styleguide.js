"use babel";

import React from 'react';
import ReactDOMServer from 'react-dom/server';
import ReactDOM from 'react-dom';
import Path from 'path';

import {Search} from './components/Search';


var styleguide = [];
window.styleguide = styleguide;
export function registerComponent(comp, props, children) {
    const list = styleguide;
    const item = list.find(el => el.type === comp);
    if (!item) {
        list.push({
            $$typeof: Symbol.for('react.element'),
            type: comp,
            props: props,
            children: children.length == 1? children[0] : children
        });
    }
}

export function patchReact(React) {
    const oldCreateElement = React.createElement.bind();
    React.createElement = function (C, props, ...children) {
        if (typeof C == 'function' && C !== Styleguide && C !== StyleguideElement) {

            registerComponent(C, props, children);
        }

        return oldCreateElement.apply(React, arguments)
    }
}

function StyleguideElement({el}) {
    const props = el.props || {};

    const sProps = '{' + Object.keys(props).join(', ') + '}';

    let renderedEl;
    try {
        renderedEl = ReactDOMServer.renderToStaticMarkup(el);
    } catch (e) {
        renderedEl = e.toString();
    }
    const path = el.type.lupaMetadata;
    const fileEl = <span
        className="btn"
        sstyle={{cursor: 'pointer', }}
        // TODO move Atom related things from out this file!
        onClick={() => atom.workspace.open(path)}>
            {Path.basename(path)}
    </span>

    return <section><h3>&lt;{el.type.name} /&gt; {fileEl}</h3>
        <h4>props: </h4><pre style={{width: 540, maxHeight: 220, overflow: 'scroll'}}>{sProps}</pre>
        <div
            style={{padding: 40, border: '1px solid grey'}}
            dangerouslySetInnerHTML={{__html: renderedEl}}
        >

        </div>
    </section>
}

export class Styleguide extends React.Component {
    constructor(props) {
        super(props);
        this.state = {filter: md => md};
    }
    handleClear() {
        //TODO
        // we're mutating global object here!!!!!!! 
        this.props.styleguide.length = 0;
        this.forceUpdate();
    }
    render() {
        const _elements = this.props.styleguide
            .map(el => ({name: el.type.name, el: el}))
            .reverse();
        const elements = this.state.filter(_elements);
        const len = styleguide.length;
        const recInfo = <span>({len} recorded)</span>;
        return <div>
        <div style={{width: 200}}>This styleguide records creation of React elements in whole package.<br/>
        If you want to refresh, you have to:<br/>
        <ol><li>press button `Clear`</li>
        <li>do something in editor, which triggers updates of React components (e.g. open JS file)</li>
         <li>return to the styleguide {/*and click `Generate` button*/}</li></ol></div>
        <button onClick={this.handleClear.bind(this)}>Clear and begin recording</button><br />
        <div>{recInfo}</div>
        <Search
            onChange={ ({phrase, filter} ) => this.setState({phrase, filter})}
            ref={search => this.search = search}
        />
        {/*<button onClick={this.handleGenerate.bind(this)}>Generate from recorded elements {recInfo}</button>*/}
        {
            elements.map(entity => <StyleguideElement el={entity.el} />)
        }
        </div>
    }
}
